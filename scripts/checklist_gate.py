# -*- coding: utf-8 -*-
"""PRD-341/T3（trend issue #1620 的 T3 环节）：十二原则 checklist 通过闸门。

按 T1 设计（docs/plans/2026-11-09-prd-341-twelve-factors-design.md）§5/R4
落地，消费 T2 skill_checklist 产物（注入式只读）：

  - GATE_CODES 词表封闭：READY_FOR_HUMAN / PENDING_MANUAL / BLOCKED /
    TAMPERED；
  - checklist_gate(report)：单 skill 通过闸门——任一机检 fail → BLOCKED
    （failing 显形）；机检全过但 manual 有未附答项 → PENDING_MANUAL
    （未答问题清单显形——**零视为通过**：manual 未答就是未答）；机检全过
    且 manual 全部附答 → READY_FOR_HUMAN（仍只是「待人工拍板」——闸门
    零替人拍板，通过动作在人）；manual 项状态被篡改为 pass/fail →
    TAMPERED 显形拒绝（R4 复核：manual 永远只能是 manual）；
  - batch_gate(reports)：全库汇总闸门（消费 T2 summarize）——任一 skill
    非 READY_FOR_HUMAN → 整库 BLOCKED/PENDING_MANUAL 归重；逐 skill 裁决
    平列（人工拍板按 skill 逐个进行）。

零网络；示例全虚构占位。
测试：tests/test_prd341_t3_gate.py
"""
from __future__ import annotations

from typing import Any

from skill_checklist import MANUAL_IDS, summarize

GATE_SCHEMA = "checklist-gate/v1"
GATE_CODES = ("READY_FOR_HUMAN", "PENDING_MANUAL", "BLOCKED", "TAMPERED")


def checklist_gate(report: dict[str, Any]) -> dict[str, Any]:
    """单 skill 通过闸门（R4）：fail 拒绝 / manual 未答留待 / 全备才荐人工。"""
    tampered = []
    for r in report.get("results", []):
        if r["id"] in MANUAL_IDS and r.get("state") != "manual":
            tampered.append({"id": r["id"], "state": r.get("state")})
    if tampered:
        return {"schema": GATE_SCHEMA, "skill": report.get("skill"),
                "gate": "TAMPERED", "failing": [], "unanswered": [],
                "tampered": tampered,
                "note": "manual 项状态被改——R4 复核拒绝（manual 只能是 manual）"}
    failing = [{"id": r["id"], "reason": r.get("reason", "")}
               for r in report.get("results", []) if r.get("state") == "fail"]
    if failing:
        return {"schema": GATE_SCHEMA, "skill": report.get("skill"),
                "gate": "BLOCKED", "failing": failing, "unanswered": [],
                "tampered": [],
                "note": "机检有未过项——如实阻断，不视为通过（R4）"}
    unanswered = [{"id": r["id"], "questions": r.get("questions", [])}
                  for r in report.get("results", [])
                  if r.get("state") == "manual" and not r.get("answers")]
    if unanswered:
        return {"schema": GATE_SCHEMA, "skill": report.get("skill"),
                "gate": "PENDING_MANUAL", "failing": [],
                "unanswered": unanswered, "tampered": [],
                "note": "人工评审项未附答——零视为通过，答完再荐（R4）"}
    return {"schema": GATE_SCHEMA, "skill": report.get("skill"),
            "gate": "READY_FOR_HUMAN", "failing": [], "unanswered": [],
            "tampered": [],
            "note": "机检全过且人工附答齐备——荐人工拍板（闸门零替人拍板）"}


def batch_gate(reports: list[dict[str, Any]]) -> dict[str, Any]:
    """全库汇总闸门：逐 skill 裁决平列 + 整库归重（任一非 READY 即不整库过）。"""
    verdicts = [checklist_gate(r) for r in reports]
    order = {"TAMPERED": 0, "BLOCKED": 1, "PENDING_MANUAL": 2,
             "READY_FOR_HUMAN": 3}
    worst = min((order[v["gate"]] for v in verdicts), default=3)
    batch = [code for code, rank in order.items() if rank == worst][0]
    summary = summarize(reports)
    return {"schema": GATE_SCHEMA, "gate": batch,
            "skills": len(verdicts), "verdicts": verdicts,
            "totals": summary["totals"],
            "note": "整库归重取最重裁决——人工拍板按 skill 逐个进行（R4）"}
