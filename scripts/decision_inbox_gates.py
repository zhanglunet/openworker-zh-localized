# -*- coding: utf-8 -*-
"""PRD-369/T3（trend issue #1648 的 T3 环节）：人工拍板收件箱批阅闸门。

按 T1 设计（docs/plans/2026-11-11-prd-369-decision-inbox-design.md）§4 落地，
消费 T2 decision_inbox 产物（注入式只读）：

  - mark_baseline + append_only_gate：events 只增不删复核——基线锚后长度
    单调不减 + 首事件原样，破坏 LEDGER_DRIFT 显形（无基线时形态检查）；
  - state_gate：条目状态与 events 双向对账——条目被直接改写、events 有
    裁决但条目回 pending、events 有裁决但条目被删，三者全部
    STATE_INCONSISTENT 显形（裁决必须双向一致）；
  - gate_summary 多闸一票否决合并显形。

**零 checklist 状态改写零代填**（R1 红线继续）：闸门只读消费零账本写零
checklist 写零注册表写零附答代填。零网络；示例全虚构占位。
测试：tests/test_prd369_t3_decision_inbox_gates.py
"""
from __future__ import annotations

from typing import Any

GATE_SCHEMA = "decision-inbox-gate/v1"
GATE_CODES = ("LEDGER_DRIFT", "STATE_INCONSISTENT", "DECISION_MISSING")


def _fail(gate: str, reasons: list[str]) -> dict[str, Any]:
    return {"schema": GATE_SCHEMA, "gate": gate, "reasons": reasons}


def mark_baseline(ledger: Any) -> None:
    """打基线锚：记录当前 events 长度与首事件（只挂只读锚属性）。"""
    events = getattr(ledger, "events", None)
    if events is None:
        raise ValueError("账本无 events 属性——非 InboxLedger")
    ledger._gate_baseline_len = len(events)
    ledger._gate_baseline_first = dict(events[0]) if events else None


def append_only_gate(ledger: Any) -> dict[str, Any]:
    """events 只增不删复核（R4 落地）。"""
    events = getattr(ledger, "events", None)
    if events is None:
        return _fail("LEDGER_DRIFT", ["账本无 events 属性——非 InboxLedger"])
    if getattr(ledger, "_gate_baseline_len", None) is not None:
        if len(events) < ledger._gate_baseline_len:
            return _fail("LEDGER_DRIFT",
                         [f"events 长度 {len(events)} < 基线 "
                          f"{ledger._gate_baseline_len}——发生删除"])
    if getattr(ledger, "_gate_baseline_first", None) is not None:
        if events and events[0] != ledger._gate_baseline_first:
            return _fail("LEDGER_DRIFT", ["首事件被改写——append-only 破坏"])
    return _fail("pass", [])


def state_gate(ledger: Any) -> dict[str, Any]:
    """条目状态与 events 双向对账（R1 落地）：裁决必须双向一致。"""
    items = ledger.view()
    events = getattr(ledger, "events", None) or []
    decided = {e["item_id"]: e["op"] for e in events
               if e.get("op") in ("approved", "rejected")}
    reasons: list[str] = []
    for it in items:
        iid = it["item_id"]
        op = decided.get(iid)
        if it["state"] != "pending" and op is None:
            reasons.append(f"{iid} 状态 {it['state']} 但 events 无对应裁决——"
                           "条目被直接改写（STATE_INCONSISTENT）")
        elif it["state"] == "pending" and op is not None:
            reasons.append(f"{iid} events 有 {op} 但条目回 pending——"
                           "状态被回滚（STATE_INCONSISTENT）")
    for iid, op in decided.items():
        it = next((x for x in items if x["item_id"] == iid), None)
        if it is None:
            reasons.append(f"{iid} events 有 {op} 但条目不在箱——"
                           "条目被删除（STATE_INCONSISTENT）")
    return _fail("pass", []) if not reasons else _fail(
        "STATE_INCONSISTENT", reasons)


def gate_summary(gates: list[dict[str, Any]]) -> dict[str, Any]:
    """多闸一票否决合并显形。"""
    reasons = [r for g in gates for r in g.get("reasons", [])]
    return {"schema": GATE_SCHEMA,
            "gate": "pass" if not reasons else "block",
            "gates_checked": len(gates), "reasons": reasons}
