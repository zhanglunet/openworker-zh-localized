# -*- coding: utf-8 -*-
"""PRD-355/T3 测试（trend #1634 的 T3 环节）：中文 skill 调用重放闸门。

运行：uv run --with pytest python -m pytest tests/test_prd355_t3_zh_call_replay_gates.py -q
（仓库根执行）

覆盖（T1 §4 + R2/R3/R4）：ledger_gate（一致 pass/verdict 或 evidence 或指纹
错位 VERDICT_MISMATCH 显形/空账本显形）；append_only_gate（无基线形态过/
mark_baseline 后追加 pass/删除或首条改写 LEDGER_DRIFT 显形）；pack_gate（一致
pass/别包冒充 PACK_STALE 显形）；gate_summary 一票否决；与 T2 串联（真实
make_pack+replay+ReplayLedger+zh_trigger_registry.lookup 产物三闸全过）；AST
零网络零子进程+闸门只读。零网络；全合成占位。
"""
import ast
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_call_replay import ReplayLedger, make_pack, replay  # noqa: E402
from zh_call_replay_gates import (  # noqa: E402
    ERROR_CODES,
    append_only_gate,
    gate_summary,
    ledger_gate,
    mark_baseline,
    pack_gate,
)
from zh_trigger_registry import build_registry, lookup  # noqa: E402

NOW = "2026-11-11T09:00:00Z"
REGISTRY = build_registry()
UTTERANCES = ["帮我写周报（占位）"]
NORMALIZED = ["帮我写周报（占位）"]
LOOKUP = lookup(REGISTRY, UTTERANCES[0])
CALLS = [{"utterance": UTTERANCES[0], "resolved_skill": LOOKUP.get("skill"),
          "status": LOOKUP["status"], "candidates": LOOKUP.get("candidates", [])}]


def lookup_fn(utt, reg):
    return lookup(reg, utt)


class TestLedgerGate:
    def _setup(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        verdict = replay(pack, UTTERANCES, REGISTRY, NORMALIZED, lookup_fn,
                         rules_version="v1")
        ledger = ReplayLedger()
        ledger.record(pack, verdict, at=NOW)
        return pack, verdict, ledger

    def test_consistent_record_passes(self):
        pack, verdict, ledger = self._setup()
        assert ledger_gate(pack, verdict, ledger)["gate"] == "pass"

    def test_forged_verdict_mismatch(self):
        """verdict 与账本不一致 → VERDICT_MISMATCH 显形。"""
        pack, _, ledger = self._setup()
        forged = {"verdict": "REPLAY_MISMATCH", "evidence": None}
        out = ledger_gate(pack, forged, ledger)
        assert out["gate"] == "VERDICT_MISMATCH"
        assert any("不一致" in r for r in out["reasons"])

    def test_tampered_evidence_mismatch(self):
        pack, _, ledger = self._setup()
        forged = {"verdict": "REPLAY_OK",
                  "evidence": {"fake": "证据改写（占位）"}}
        out = ledger_gate(pack, forged, ledger)
        assert out["gate"] == "VERDICT_MISMATCH"

    def test_empty_ledger_visible(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        out = ledger_gate(pack, {"verdict": "REPLAY_OK", "evidence": None},
                          ReplayLedger())
        assert out["gate"] == "VERDICT_MISMATCH"
        assert "账本为空" in out["reasons"][0]


class TestAppendOnlyGate:
    def _setup(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        ledger = ReplayLedger()
        ledger.record(pack, {"verdict": "REPLAY_OK", "evidence": None},
                      at=NOW)
        ledger.record(pack, {"verdict": "REPLAY_OK", "evidence": None},
                      at=NOW)
        return pack, ledger

    def test_no_baseline_form_check_passes(self):
        _, ledger = self._setup()
        assert append_only_gate(ledger)["gate"] == "pass"

    def test_mark_baseline_then_append_passes(self):
        pack, ledger = self._setup()
        mark_baseline(ledger)
        ledger.record(pack, {"verdict": "REPLAY_OK", "evidence": None},
                      at=NOW)
        assert append_only_gate(ledger)["gate"] == "pass"

    def test_deletion_detected(self):
        _, ledger = self._setup()
        mark_baseline(ledger)
        ledger._entries.pop()
        assert append_only_gate(ledger)["gate"] == "LEDGER_DRIFT"

    def test_first_entry_rewrite_detected(self):
        _, ledger = self._setup()
        mark_baseline(ledger)
        ledger._entries[0]["verdict"] = "REPLAY_OK（篡改）（占位）"
        assert append_only_gate(ledger)["gate"] == "LEDGER_DRIFT"

    def test_non_ledger_object_visible(self):
        assert append_only_gate(object())["gate"] == "LEDGER_DRIFT"


class TestPackGate:
    def _setup(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        ledger = ReplayLedger()
        ledger.record(pack, {"verdict": "REPLAY_OK", "evidence": None},
                      at=NOW)
        return pack, ledger

    def test_matching_pack_passes(self):
        pack, ledger = self._setup()
        assert pack_gate(pack, ledger)["gate"] == "pass"

    def test_wrong_pack_stale(self):
        """别包冒充 → PACK_STALE 显形（不同登记册 → 不同指纹）。"""
        other = make_pack(CALLS, {"entries": []}, NORMALIZED,
                          rules_version="v1")
        _, ledger = self._setup()
        assert pack_gate(other, ledger)["gate"] == "PACK_STALE"

    def test_empty_ledger_visible(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        assert pack_gate(pack, ReplayLedger())["gate"] == "PACK_STALE"


class TestSummaryAndChain:
    def test_summary_one_block_votes_all(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        ledger = ReplayLedger()
        ledger.record(pack, {"verdict": "REPLAY_OK", "evidence": None},
                      at=NOW)
        forged = {"verdict": "REPLAY_OK", "evidence": {"fake": 1}}
        out = gate_summary([append_only_gate(ledger),
                            ledger_gate(pack, forged, ledger)])
        assert out["gate"] == "block"
        assert out["gates_checked"] == 2

    def test_chain_with_real_t2_products(self):
        """与 T2 串联：真实 make_pack+replay（lookup）+ReplayLedger 三闸全过。"""
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        verdict = replay(pack, UTTERANCES, REGISTRY, NORMALIZED, lookup_fn,
                         rules_version="v1")
        ledger = ReplayLedger()
        ledger.record(pack, verdict, at=NOW)
        mark_baseline(ledger)
        results = [append_only_gate(ledger), ledger_gate(pack, verdict, ledger),
                   pack_gate(pack, ledger)]
        assert all(r["gate"] == "pass" for r in results)
        assert gate_summary(results)["gate"] == "pass"

    def test_error_codes_closed(self):
        assert set(ERROR_CODES) == {"VERDICT_MISMATCH", "LEDGER_DRIFT",
                                    "PACK_STALE"}


class TestRedline:
    def test_ast_zero_network_zero_subprocess_readonly(self):
        """R2 AST：零网络零子进程+闸门只读（零账本写调用）。"""
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        src = (REPO / "scripts" / "zh_call_replay_gates.py").read_text(
            encoding="utf-8")
        tree = ast.parse(src)
        for node in ast.walk(tree):
            mods = []
            if isinstance(node, ast.Import):
                mods = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                mods = [node.module.split(".")[0]]
            for mod in mods:
                assert mod not in banned
        for call in (".record(", ".add(", ".append("):
            assert call not in src, f"闸门出现账本写调用 {call}"


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
