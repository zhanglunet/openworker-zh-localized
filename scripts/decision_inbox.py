# -*- coding: utf-8 -*-
"""PRD-369/T2（trend issue #1648 的 T2 环节）：人工拍板收件箱最小实现。

按 T1 设计（docs/plans/2026-11-11-prd-369-decision-inbox-design.md）
§3.1/§3.2/§4 实现：

  - collect(*, manual_reviews=None, answer_confirms=None,
    zh_disambiguations=None)：三源只读汇聚（R2）——checklist P10–P12 人工
    评审项（PRD-341 荐人工拍板零替人拍板）、附答后的人工确认（answers_ref
    引用 341 manual_answers 留痕）、中文歧义候选 → 条目五件套 {item_id,
    kind, source_ref, fingerprint, questions?/candidates?, reason, state}
    缺一 INBOX_ITEM_INCOMPLETE 拒绝入箱（R3）；
  - approve(item, *, by, at, choice=None)：歧义项必带选中候选且候选须在
    列表内（INBOX_CHOICE_REQUIRED）；**零 checklist 状态改写零附答代填**
    （§6.1 裁决：收件箱零代填——人再走 run_checklist 附答或收件箱仅引用
    answers_ref）；
  - InboxLedger：append-only（R4）——add/approve/reject 人批留痕；重复
    裁决 INBOX_DOUBLE_DECIDE、未知 id、携带 checklist 写/注册表写/附答代填
    载荷 INBOX_AUTO_EXEC_ATTEMPT（R1 零自动执行）显形拒绝；
  - view(kind)：kind 过滤视图。

kind 词表封闭：manual_review / answer_confirm / zh_disambiguation。
零网络；示例全虚构占位。
测试：tests/test_prd369_t2_decision_inbox.py
"""
from __future__ import annotations

import copy
from typing import Any

INBOX_SCHEMA = "decision-inbox/v1"
ITEM_KINDS = ("manual_review", "answer_confirm", "zh_disambiguation")
ERROR_CODES = ("INBOX_ITEM_INCOMPLETE", "INBOX_DOUBLE_DECIDE",
               "INBOX_AUTO_EXEC_ATTEMPT", "INBOX_CHOICE_REQUIRED")
_EXEC_KEYS = ("action", "execute", "write_checklist", "write_registry",
              "fill_answers")


class InboxError(ValueError):
    """收件箱违规——显形拒绝。"""


def _item(item_id: str, kind: str, source_ref: str, fingerprint: str,
          reason: str, questions: list | None = None,
          candidates: list | None = None,
          answers_ref: str | None = None) -> dict[str, Any]:
    return {"item_id": item_id, "kind": kind, "source_ref": source_ref,
            "fingerprint": fingerprint, "questions": questions or [],
            "candidates": candidates or [], "answers_ref": answers_ref,
            "reason": reason, "state": "pending",
            "decided_by": None, "decided_at": None, "reject_reason": None,
            "chosen_candidate": None}


def collect(*, manual_reviews: list[dict[str, Any]] | None = None,
            answer_confirms: list[dict[str, Any]] | None = None,
            zh_disambiguations: list[dict[str, Any]] | None = None,
            fingerprint: str = "sha16:none（占位）",
            at: str = "") -> list[dict[str, Any]]:
    """三源只读汇聚（R2）；五件套缺一拒绝入箱并显形。"""
    items: list[dict[str, Any]] = []
    incomplete: list[str] = []
    n = 0

    def _add(kind: str, source_ref: str, fp: str, reason: str,
             questions: list | None = None, candidates: list | None = None,
             answers_ref: str | None = None):
        nonlocal n
        n += 1
        it = _item(f"item-{n:03d}", kind, source_ref, fp, reason, questions,
                   candidates, answers_ref)
        missing = [k for k in ("item_id", "kind", "source_ref", "fingerprint",
                               "reason") if not it.get(k)]
        if missing or kind not in ITEM_KINDS:
            incomplete.append(f"{kind or '(空 kind)'} 缺 {missing or 'kind 非法'}")
            return
        items.append(it)

    for m in manual_reviews or []:
        _add("manual_review",
             str(m.get("source_ref") or "skill-checklist-report/v1（占位）"),
             str(m.get("fingerprint") or fingerprint),
             str(m.get("reason") or "P10–P12 人工评审项（占位）"),
             questions=m.get("questions") or [])
    for a in answer_confirms or []:
        _add("answer_confirm",
             str(a.get("source_ref") or "manual-answers（占位）"),
             str(a.get("fingerprint") or fingerprint),
             str(a.get("reason") or "附答后待人工确认（占位）"),
             answers_ref=a.get("answers_ref") or "")
    for z in zh_disambiguations or []:
        _add("zh_disambiguation", str(z.get("source_ref") or "ref-resolution"),
             str(z.get("fingerprint") or fingerprint),
             str(z.get("reason") or "中文歧义候选（占位）"),
             candidates=z.get("candidates") or [])
    if incomplete:
        raise InboxError(f"INBOX_ITEM_INCOMPLETE：{'；'.join(incomplete)}")
    return items


class InboxLedger:
    """收件箱账本（R4）：append-only；approve/reject 只改状态零代写（R1）。"""

    def __init__(self) -> None:
        self._items: dict[str, dict[str, Any]] = {}
        self._events: list[dict[str, Any]] = []

    def add(self, items: list[dict[str, Any]]) -> list[str]:
        added = []
        for it in items:
            if it["item_id"] in self._items:
                raise InboxError(f"INBOX_DOUBLE_DECIDE：{it['item_id']} 已在箱")
            self._items[it["item_id"]] = copy.deepcopy(it)
            self._events.append({"op": "add", "item_id": it["item_id"]})
            added.append(it["item_id"])
        return added

    def _decide(self, item_id: str, state: str, *, by: str, at: str,
                reason: str = "", choice: str | None = None,
                payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if payload and any(k in payload for k in _EXEC_KEYS):
            raise InboxError("INBOX_AUTO_EXEC_ATTEMPT：裁决携带 checklist 写/"
                             "注册表写/附答代填载荷——收件箱零自动执行（R1），"
                             "manual 仍是 manual（PRD-341 TAMPERED 红线继续）")
        it = self._items.get(item_id)
        if not it:
            raise InboxError(f"未知 item_id：{item_id!r}")
        if it["state"] != "pending":
            raise InboxError(f"INBOX_DOUBLE_DECIDE：{item_id} 已裁决"
                             f"（{it['state']}）——重复裁决显形拒绝")
        if state == "approved" and it["kind"] == "zh_disambiguation":
            if not choice:
                raise InboxError("INBOX_CHOICE_REQUIRED：歧义项 approve 必带"
                                 "选中候选")
            if choice not in it["candidates"]:
                raise InboxError(f"INBOX_CHOICE_REQUIRED：候选 {choice!r} 不在"
                                 "候选列表")
            it["chosen_candidate"] = choice
        it["state"] = state
        it["decided_by"] = by
        it["decided_at"] = at
        if reason:
            it["reject_reason"] = reason
        self._events.append({"op": state.lower(), "item_id": item_id,
                             "by": by, "at": at})
        return dict(it)

    def approve(self, item_id: str, *, by: str, at: str,
                choice: str | None = None,
                payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._decide(item_id, "approved", by=by, at=at, choice=choice,
                            payload=payload)

    def reject(self, item_id: str, *, by: str, at: str, reason: str = "",
              payload: dict[str, Any] | None = None) -> dict[str, Any]:
        return self._decide(item_id, "rejected", by=by, at=at, reason=reason,
                            payload=payload)

    def view(self, kind: str | None = None) -> list[dict[str, Any]]:
        return [copy.deepcopy(it) for it in self._items.values()
                if kind is None or it["kind"] == kind]

    @property
    def events(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self._events]
