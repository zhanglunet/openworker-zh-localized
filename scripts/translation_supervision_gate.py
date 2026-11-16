# -*- coding: utf-8 -*-
"""PRD-452/T3（trend issue #2157 的 T3 环节）：翻译监督台监督回路闸门。

按 T1 设计 §5 关口规则落地：人工拍板收件箱入口的强制检查。闸门不读译稿
的 status 位，只从 decisions/feedbacks/annotations 原始记录重新推导「这段
译稿是否已点头且批注全闭环」（fail-closed，任一存疑即拦下）：

  1. 无点头裁决记录 → GATE_NO_DECISION（手写 status 位不作数）；
  2. 存在未处理批注（待处理）→ GATE_ANNOTATION_OPEN；
  3. 存在未闭环反馈单（待处理/待回炉无新版）→ GATE_FEEDBACK_OPEN；
  4. 点头版本不是最新版本 → GATE_NOT_LATEST_VERSION（旧版本点头不外流，
     新版本须重新审）。

T2 的 outlet 保留（只看状态位）；生产出口应走本闸门 admit_via_gate()。
零 LLM 零网络零子进程；示例全虚构占位。
测试：tests/test_prd452_t3_translation_supervision_gate.py
"""
from __future__ import annotations

from typing import Any

GATE_SCHEMA = "translation-supervision-gate/v1"
GATE_REASONS = ("GATE_ALLOWED", "GATE_NO_DECISION", "GATE_ANNOTATION_OPEN",
                "GATE_FEEDBACK_OPEN", "GATE_NOT_LATEST_VERSION")


def _verdict(source_seq: str, allowed: bool, reason: str,
             detail: str) -> dict[str, Any]:
    return {"schema": GATE_SCHEMA, "source_seq": source_seq,
            "allowed": allowed, "reason": reason, "detail": detail}


def evaluate(source_seq: str, decisions: list[dict[str, Any]],
             annotations: list[dict[str, Any]],
             feedbacks: list[dict[str, Any]],
             versions: list[dict[str, Any]]) -> dict[str, Any]:
    """从裁决/批注/反馈/版本原始记录重导单段译稿的放行结论（fail-closed）。"""
    decisions = decisions or []
    annotations = annotations or []
    feedbacks = feedbacks or []
    versions = versions or []
    rel = [d for d in decisions if d.get("source_seq") == source_seq]
    if not rel:
        return _verdict(source_seq, False, "GATE_NO_DECISION",
                        "无点头裁决记录——手写 status 位不作数")
    latest_version = (versions[-1].get("version") if versions else None)
    if latest_version and rel[-1].get("version") != latest_version:
        return _verdict(source_seq, False, "GATE_NOT_LATEST_VERSION",
                        f"点头版本 {rel[-1].get('version')!r} 非最新 "
                        f"{latest_version!r}——旧版本点头不外流")
    open_annot = [a for a in annotations if a.get("status") == "待处理"]
    if open_annot:
        return _verdict(source_seq, False, "GATE_ANNOTATION_OPEN",
                        f"{len(open_annot)} 条批注未处理")
    open_fb = [f for f in feedbacks if f.get("status") == "待处理"]
    if open_fb:
        return _verdict(source_seq, False, "GATE_FEEDBACK_OPEN",
                        f"{len(open_fb)} 条反馈单待处理")
    return _verdict(source_seq, True, "GATE_ALLOWED", "裁决与批注闭环齐备")


def admit_via_gate(bench: Any) -> dict[str, Any]:
    """人工拍板收件箱入口（R1）：整段译稿过闸，fail-closed。"""
    source_seq = str(getattr(bench, "source_seq", ""))
    verdict = evaluate(source_seq, getattr(bench, "decisions", []),
                       getattr(bench, "annotations", []),
                       getattr(bench, "feedbacks", []),
                       getattr(bench, "versions", []))
    if verdict["allowed"]:
        latest = bench.versions[-1]
        return {"schema": GATE_SCHEMA, "passed": [{
            "source_seq": source_seq, "version": latest["version"],
            "text": latest["text"], "gate": verdict["reason"]}],
            "blocked": [], "blocked_count": 0}
    return {"schema": GATE_SCHEMA, "passed": [],
            "blocked": [{"source_seq": source_seq, "gate": verdict["reason"],
                         "detail": verdict["detail"]}],
            "blocked_count": 1}
