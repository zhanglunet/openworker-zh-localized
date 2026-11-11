# -*- coding: utf-8 -*-
"""PRD-355/T2（trend issue #1634 的 T2 环节）：中文 skill 调用重放包最小实现。

按 T1 设计（docs/plans/2026-11-11-prd-355-zh-call-replay-design.md）
§3.1/§3.2/§4 实现：

  - make_pack(calls, registry, *, rules_version)：从中文调用决策记录构建
    重放包（R1 三件套）——input_fingerprint（指令原文 digest + 归一化
    digest + 登记册 digest + rules_version 三重指纹）、decisions（解析到的
    技能包 + 触发词命中 + 歧义候选处理逐条）、output（resolved/refused 汇总）；
    缺任一 PACK_INCOMPLETE；
  - replay(pack, utterances, registry, lookup_fn, *, rules_version)：重放三步
    （§3.2）——①三重指纹复核（原文/归一化/登记册 digest 或版本不符 →
    REPLAY_INPUT_DRIFT 拒绝，MISMATCH 时可区分「原文同但归一化变」vs
    「登记册变」）②注入式 lookup_fn 深拷贝复算解析层（zh_trigger_registry
    .lookup 形态，零 skill 执行零网络 R2）③decisions 逐字节比对 →
    REPLAY_OK / REPLAY_MISMATCH（首分歧条显形，R3 零静默换新解析）；
  - ReplayLedger：append-only（R4）。

零网络；示例全虚构占位。
测试：tests/test_prd355_t2_zh_call_replay.py
"""
from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Callable

PACK_SCHEMA = "zh-call-replay-pack/v1"
ERROR_CODES = ("REPLAY_INPUT_DRIFT", "REPLAY_MISMATCH", "PACK_INCOMPLETE")
_DECISION_KEYS = ("utterance", "resolved_skill", "status")


def _digest(payload: Any) -> str:
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                           separators=(",", ":"))
    return "sha16:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def registry_digest(registry: dict[str, Any]) -> str:
    return _digest(registry)


def make_pack(calls: list[dict[str, Any]], registry: dict[str, Any],
              normalized: list[str], *, rules_version: str) -> dict[str, Any]:
    """从中文调用决策记录构建重放包（R1 三件套，三重指纹）。"""
    clean = []
    for c in calls or []:
        if not isinstance(c.get("utterance"), str) or c.get("status") is None:
            return {"schema": PACK_SCHEMA, "refused": "PACK_INCOMPLETE",
                    "detail": "决策缺 utterance/status——拒绝入账"}
        clean.append({k: c.get(k) for k in
                      ("utterance", "resolved_skill", "status", "candidates")})
    if (not clean or not registry or not rules_version
            or len(normalized) != len(clean)):
        return {"schema": PACK_SCHEMA, "refused": "PACK_INCOMPLETE",
                "detail": "calls/registry/normalized/rules_version 缺失或长度不齐"}
    return {
        "schema": PACK_SCHEMA,
        "input_fingerprint": {
            "utterances_digest": _digest([c["utterance"] for c in clean]),
            "normalized_digest": _digest(normalized),
            "registry_digest": registry_digest(registry),
            "rules_version": rules_version},
        "decisions": clean,
        "output": {"statuses": [c["status"] for c in clean],
                   "resolved": [c["resolved_skill"] for c in clean]},
    }


def _refusal(code: str, detail: str) -> dict[str, Any]:
    return {"schema": PACK_SCHEMA, "refused": code, "detail": detail,
            "verdict": None}


def replay(pack: dict[str, Any], utterances: list[str],
           registry: dict[str, Any], normalized: list[str],
           lookup_fn: Callable[[str, dict], dict[str, Any]], *,
           rules_version: str) -> dict[str, Any]:
    """重放三步（§3.2）：解析层复算（R2 零 skill 执行），对不上显形（R3）。

    三重指纹区分漂移来源：原文同但归一化变 vs 登记册变（R3 证据线索）。
    """
    fp = pack.get("input_fingerprint") or {}
    if (not fp or pack.get("refused") or not pack.get("decisions")
            or not pack.get("output")):
        return _refusal("PACK_INCOMPLETE", "重放包三件套不齐")
    utt_digest = _digest(utterances)
    norm_digest = _digest(normalized)
    reg_digest = registry_digest(registry)
    if utt_digest != fp.get("utterances_digest"):
        return _refusal("REPLAY_INPUT_DRIFT", "指令原文与包不符——拒绝重放")
    if reg_digest != fp.get("registry_digest"):
        return _refusal("REPLAY_INPUT_DRIFT", "登记册与包不符——拒绝重放"
                        "（漂移来源线索：登记册变）")
    if (norm_digest != fp.get("normalized_digest")
            or rules_version != fp.get("rules_version")):
        return _refusal("REPLAY_INPUT_DRIFT",
                        "归一化/版本与包不符——拒绝重放"
                        "（漂移来源线索：原文同但归一化变）")
    rerun = []
    for utt in utterances:
        out = lookup_fn(copy.deepcopy(utt), copy.deepcopy(registry))
        rerun.append({"utterance": utt,
                      "resolved_skill": out.get("skill"),
                      "status": out.get("status"),
                      "candidates": out.get("candidates", [])})
    for i, want in enumerate(pack["decisions"]):
        got = rerun[i] if i < len(rerun) else None
        if got != want:
            return {"schema": PACK_SCHEMA, "refused": None,
                    "verdict": "REPLAY_MISMATCH",
                    "evidence": {"first_divergence_index": i,
                                 "want": want, "got": got},
                    "rerun_count": len(rerun)}
    if len(rerun) != len(pack["decisions"]):
        return {"schema": PACK_SCHEMA, "refused": None,
                "verdict": "REPLAY_MISMATCH",
                "evidence": {"first_divergence_index": len(rerun),
                             "why": "决策条数不一致"},
                "rerun_count": len(rerun)}
    return {"schema": PACK_SCHEMA, "refused": None, "verdict": "REPLAY_OK",
            "evidence": None, "rerun_count": len(rerun)}


class ReplayLedger:
    """重放账本（R4）：append-only 只增不删。"""

    def __init__(self) -> None:
        self._entries: list[dict[str, Any]] = []

    def record(self, pack: dict[str, Any], verdict: dict[str, Any], *,
               at: str) -> dict[str, Any]:
        entry = {"at": at,
                 "pack_fingerprint": copy.deepcopy(pack.get("input_fingerprint")),
                 "verdict": verdict.get("verdict") or verdict.get("refused"),
                 "evidence": copy.deepcopy(verdict.get("evidence"))}
        self._entries.append(entry)
        return dict(entry)

    @property
    def entries(self) -> list[dict[str, Any]]:
        return [dict(e) for e in self._entries]
