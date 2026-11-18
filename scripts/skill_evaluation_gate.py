"""PRD-488/T3（trend issue #2362 的 T3 环节）：中文技能评估 监督回路闸门。

按 T1 设计（docs/plans/2026-11-17-prd-488-owzh-skill-evaluation-design.md）
§五/§七落地：把"评估未过关的技能不得进入下游"做成人工审稿入口前的强制检查。

为什么 T2 还不够：T2 只产出评估报告——质量门结论、疑似重叠、整改候选都写在
报告里，但没有任何东西拦住未过关技能的产物进人工审稿。报告说"证据不足"也好、
"整改"也好，下游只要不看报告就能照常用该技能出产物。

T3 的做法（只加检查，不改 T2 的评估逻辑与报告格式，按技能过闸）：
  - check_gate(report, skill_id)：纯函数，不改报告；以 T2 报告的 verdicts 为准
    重新推导"该技能是否可进下游"——结论是"通过" + 不在疑似重叠对里，两项
    缺一不可；只认"技能在清单里"或只认"曾经通过"的一律拦下，并逐条给出
    拦截原因（code + target + detail）。
  - enforce_gate：不通过即显形拒绝（GateError，GATE_BLOCKED）。
  - admit_to_downstream：人工审稿唯一允许的入口——先过闸，再把放行/拦截
    的审计条目写进 SkillEvaluationLedger（拦截也留痕，绕关尝试有据可查）；
    结论为"整改"而被拦的技能，另追加一条整改条目（append-only，原因/证据/
    整改期限/复测结果齐全，期限待人填、不编造）。
  - gate_outlet：加固版批量出口，逐技能过闸；只放行 check_gate 通过的技能，
    未知/残缺技能按拦截处理，永不抛错漏放。
  - 整改清单 append-only：SkillEvaluationLedger 只追加、不改历史条目；
    format_remediation_line 把整改条目渲染成 remediation-log.md 的行格式。

口径（按 T1 设计目标"中文技能包定期体检，坏技能进清单修，人工只审评估过关的技能出的译稿。"）：
  - "通过"才放行；"整改"拦下并进整改清单；"证据不足"也拦下——证据不足
    不是失效，不进整改清单，只等对照跑分补测（报告 §四原话）；疑似重叠
    拦下待人确认（设计稿 §二：行为层确认与合并/拆分/保留分工由人决定）。
    报告缺 suspected 列表按 BAD_REPORT 拦下——缺重叠结果不得放行。
    因此今天全部 11 个技能都是"证据不足"，闸门会把它们全拦下——这是实情，
    不是闸门太严：真实对照跑分在 T5 补，跑分出来重评通过后才能放行。
  - 报告没有逐技能版本字段（清单里技能只有 id，没有 version），闸门暂按
    结论裁决，并在审计里记报告日期与清单版本；清单补版本字段后可收紧。

本模块不重跑评估、不改报告、不改清单、不碰技能包——只有检查与审计，没有
放行的后门；评估结论的改动仍走 T2 的评估流程；发布仍人工确认。
零网络零子进程；示例全虚构占位。
测试：tests/test_skill_evaluation_gate.py
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

from skill_evaluation import VERDICT_INSUFFICIENT, VERDICT_PASS, VERDICT_REMEDIATE

GATE_SCHEMA = "skill-evaluation-gate/v1"
GATE_PRD = 488
GATE_REPO = "openworker-zh-localized"
BLOCK_REASON_CODES = ("BAD_REPORT", "UNKNOWN_SKILL", "REMEDIATE",
                      "INSUFFICIENT_EVIDENCE", "SUSPECTED_OVERLAP")
GATE_AUDIT_KINDS = ("gate_passed", "gate_blocked", "remediation")
VERDICTS = (VERDICT_PASS, VERDICT_REMEDIATE, VERDICT_INSUFFICIENT)


class GateError(ValueError):
    """评估闸门违规——显形拒绝。"""


def _now(at: str) -> str:
    return at or "1970-01-01T00:00:00Z"


def _reason(code: str, target: Any, detail: str) -> dict[str, Any]:
    return {"code": code, "target": target, "detail": detail}


def _verdict_for(report: dict[str, Any],
                 skill_id: str) -> dict[str, Any] | None:
    for v in report.get("verdicts") or []:
        if isinstance(v, dict) and v.get("id") == skill_id:
            return v
    return None


def _suspected_skills(report: dict[str, Any]) -> set[str]:
    found: set[str] = set()
    for p in report.get("suspected") or []:
        if not isinstance(p, dict) or not p.get("suspected"):
            continue
        for key in ("a", "b"):
            if isinstance(p.get(key), str) and p[key]:
                found.add(p[key])
    return found


def check_gate(report: dict[str, Any] | None,
               skill_id: str) -> dict[str, Any]:
    """强制复核：以 T2 报告为准重新推导"该技能是否可进下游"，不只认清单。

    返回 {"allowed": bool, "reasons": [...]}；报告残缺时只拦下不抛错；
    技能不在报告里则显形拒绝（UNKNOWN_SKILL）。
    """
    if not isinstance(report, dict):
        return {"allowed": False,
                "reasons": [_reason("BAD_REPORT", None, "评估报告不是 dict")]}
    if report.get("prd") != GATE_PRD or report.get("repo") != GATE_REPO:
        return {"allowed": False,
                "reasons": [_reason(
                    "BAD_REPORT", report.get("prd"),
                    f"评估报告非 PRD-{GATE_PRD}（{GATE_REPO}）")]}
    if not isinstance(report.get("verdicts"), list):
        return {"allowed": False,
                "reasons": [_reason("BAD_REPORT", skill_id, "报告无 verdicts 列表")]}
    if not isinstance(report.get("suspected"), list):
        return {"allowed": False,
                "reasons": [_reason("BAD_REPORT", skill_id, "报告无 suspected 列表")]}
    verdict = _verdict_for(report, skill_id)
    if verdict is None:
        raise GateError(f"UNKNOWN_SKILL：报告里无此技能 skill_id={skill_id!r}")
    reasons: list[dict[str, Any]] = []
    conclusion = verdict.get("verdict")
    if conclusion == VERDICT_REMEDIATE:
        reasons.append(_reason(
            "REMEDIATE", skill_id,
            f"技能 {skill_id!r} 质量门未过关：{verdict.get('reason')}"))
    elif conclusion == VERDICT_INSUFFICIENT:
        reasons.append(_reason(
            "INSUFFICIENT_EVIDENCE", skill_id,
            f"技能 {skill_id!r} 证据不足，未过关：{verdict.get('reason')}"))
    elif conclusion != VERDICT_PASS:
        reasons.append(_reason(
            "BAD_REPORT", skill_id,
            f"技能 {skill_id!r} 结论词表外 verdict={conclusion!r}"))
    if skill_id in _suspected_skills(report):
        reasons.append(_reason(
            "SUSPECTED_OVERLAP", skill_id,
            f"技能 {skill_id!r} 在疑似重叠对里，待人确认（不自动合并）"))
    return {"allowed": not reasons, "reasons": reasons}


def enforce_gate(report: dict[str, Any] | None,
                 skill_id: str) -> dict[str, Any]:
    """过闸：不通过即显形拒绝；通过返回 check_gate 的裁决。"""
    verdict = check_gate(report, skill_id)
    if not verdict["allowed"]:
        codes = "; ".join(
            f"{r['code']}({r['target']})" for r in verdict["reasons"])
        raise GateError(f"GATE_BLOCKED：评估未过关不进下游——{codes}")
    return verdict


def _record_decision(ledger: Any, report: dict[str, Any] | None,
                     skill_id: str, verdict: dict[str, Any],
                     by: str, at: str) -> None:
    """记一条闸门审计；结论为"整改"而被拦时，另追加一条整改条目。"""
    entry = {"kind": "gate_passed" if verdict["allowed"] else "gate_blocked",
             "skill_id": skill_id, "by": by, "at": _now(at),
             "reasons": [r["code"] for r in verdict["reasons"]],
             "targets": [r["target"] for r in verdict["reasons"]]}
    ledger.record(report if isinstance(report, dict) else {}, entry)
    if verdict["allowed"]:
        return
    if not any(r["code"] == "REMEDIATE" for r in verdict["reasons"]):
        return
    reason = next((r["detail"] for r in verdict["reasons"]
                   if r["code"] == "REMEDIATE"), "")
    date = report.get("date") if isinstance(report, dict) else None
    version = report.get("inventory_version") if isinstance(report, dict) else None
    ledger.record(report if isinstance(report, dict) else {}, {
        "kind": "remediation", "skill_id": skill_id, "by": by,
        "at": _now(at), "verdict": VERDICT_REMEDIATE, "reason": reason,
        "evidence": f"评估报告 {date or '未知日期'}，清单 v{version or '未知'}",
        "due": "待定", "action": "修", "retest": None})


def admit_to_downstream(report: dict[str, Any] | None, skill_id: str, *,
                        ledger: Any = None, by: str,
                        at: str = "") -> dict[str, Any]:
    """人工审稿唯一允许的入口：先过闸，再把裁决写进账本留痕。

    放行返回 {"admitted": 技能准入记录, "verdict": 裁决}；拦截时先记一条
    gate_blocked 审计（绕关尝试有据可查），再显形拒绝；结论为"整改"而
    被拦的技能另追加一条整改条目（append-only）。未知技能也先记账再拒绝，
    不让绕关尝试悄悄溜走。ledger 给了就必须给 by（审计须署名），否则拒绝入账。
    """
    try:
        verdict = check_gate(report, skill_id)
    except GateError as exc:
        # 未知技能：check_gate 显形拒绝在先；先把这次绕关尝试记进账本再拒绝。
        verdict = {"allowed": False,
                   "reasons": [_reason("UNKNOWN_SKILL", skill_id, str(exc))]}
    if ledger is not None:
        if not by:
            raise GateError("GATE_BLOCKED：审计留痕须 by（裁决人必填）")
        _record_decision(ledger, report, skill_id, verdict, by, at)
    if not verdict["allowed"]:
        codes = "; ".join(
            f"{r['code']}({r['target']})" for r in verdict["reasons"])
        raise GateError(f"GATE_BLOCKED：评估未过关不进下游——{codes}")
    record = _verdict_for(report, skill_id)
    return {"admitted": {
        "skill_id": skill_id,
        "verdict": record.get("verdict") if isinstance(record, dict) else None,
        "report_date": report.get("date") if isinstance(report, dict) else None,
        "inventory_version": (report.get("inventory_version")
                              if isinstance(report, dict) else None)},
        "verdict": verdict}


def gate_outlet(report: dict[str, Any] | None,
                skill_ids: list[str] | None, *,
                ledger: Any = None, by: str,
                at: str = "") -> dict[str, Any]:
    """加固版批量出口：逐技能过闸，只放行 check_gate 通过的技能。

    blocked 条目带逐条拦截原因；未知/残缺技能按拦截处理，永不抛错漏放。
    给了 ledger 则放行与拦截各记一条审计（kind=gate_passed/gate_blocked），
    结论为"整改"而被拦的技能另追加一条整改条目。
    """
    passed, blocked = [], []
    for skill_id in skill_ids or []:
        try:
            verdict = check_gate(report, skill_id)
        except GateError as exc:
            verdict = {"allowed": False,
                       "reasons": [_reason("UNKNOWN_SKILL", skill_id, str(exc))]}
        if ledger is not None:
            if not by:
                raise GateError("GATE_BLOCKED：审计留痕须 by（裁决人必填）")
            _record_decision(ledger, report, skill_id, verdict, by, at)
        if verdict["allowed"]:
            record = _verdict_for(report, skill_id)
            passed.append({
                "skill_id": skill_id,
                "verdict": record.get("verdict") if isinstance(record, dict) else None,
                "report_date": report.get("date") if isinstance(report, dict) else None,
                "inventory_version": (report.get("inventory_version")
                                      if isinstance(report, dict) else None)})
        else:
            blocked.append({"skill_id": skill_id,
                            "verdict": next(
                                (v.get("verdict") for v in
                                 (report.get("verdicts") or [])
                                 if isinstance(v, dict)
                                 and v.get("id") == skill_id), None)
                            if isinstance(report, dict) else None,
                            "reasons": verdict["reasons"]})
    return {"schema": GATE_SCHEMA, "passed": passed, "blocked": blocked,
            "blocked_count": len(blocked)}


def format_remediation_line(entry: dict[str, Any]) -> str:
    """整改条目 → remediation-log.md 的行格式（只渲染，不改历史条目）。"""
    date = str(entry.get("at") or "")[:10] or "未知日期"
    retest = entry.get("retest")
    return (f"- {date} 技能 {entry.get('skill_id')}：{entry.get('reason')} / "
            f"证据（{entry.get('evidence')}）/ 整改期限 {entry.get('due')} / "
            f"建议动作 {entry.get('action')} / 复测结果 {retest or '待复测'}")


class SkillEvaluationLedger:
    """评估闸门留痕账本：JSONL append-only（路径注入），缺件拒绝入账。

    三种条目：gate_passed / gate_blocked（闸门审计）、remediation（整改条目）。
    只追加、不改历史条目；entries() 返回深拷贝，改返回结果不污染账本。
    """

    _REQUIRED = ("skill_id", "kind", "by", "at")

    def __init__(self, path: str | Path | None = None) -> None:
        self._records: list[dict[str, Any]] = []
        self._path = Path(path) if path else None

    def record(self, report: dict[str, Any] | None,
               entry: dict[str, Any]) -> dict[str, Any]:
        report = report if isinstance(report, dict) else {}
        rec = {"schema": GATE_SCHEMA, "prd": report.get("prd"),
               "report_date": report.get("date"),
               "inventory_version": report.get("inventory_version"),
               **copy.deepcopy(entry)}
        missing = [k for k in self._REQUIRED
                   if k not in rec or rec.get(k) in (None, "")]
        if missing:
            raise GateError(f"GATE_BLOCKED：账目缺 {missing}")
        self._records.append(copy.deepcopy(rec))
        if self._path is not None:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with open(self._path, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False,
                                    sort_keys=True) + "\n")
        return dict(rec)

    def entries(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self._records)

    def latest_for(self, skill_id: str) -> dict[str, Any] | None:
        found = [r for r in self._records
                 if r.get("skill_id") == skill_id]
        return copy.deepcopy(found[-1]) if found else None
