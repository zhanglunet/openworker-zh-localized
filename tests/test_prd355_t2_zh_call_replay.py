# -*- coding: utf-8 -*-
"""PRD-355/T2 测试（trend #1634 的 T2 环节）：中文 skill 调用重放包。

运行：uv run --with pytest python -m pytest tests/test_prd355_t2_zh_call_replay.py -q
（仓库根执行）

覆盖（T1 §3.1/§3.2/§4 + R1–R4）：三件套构建（决策缺字段/长度不齐
PACK_INCOMPLETE）；重放三步（同指令同登记册同归一化 REPLAY_OK/三重指纹分别
漂移 INPUT_DRIFT 且漂移来源线索可区分——原文/登记册/归一化/决策漂移 MISMATCH
首分歧条显形含候选）；R2 重放零 skill 执行（与 zh_trigger_registry.lookup +
zh_trigger_registry.build_registry 真实串联解析层复算）；R4 账本 append-only；
AST 零网络零子进程。零网络；全合成占位。
"""
import ast
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_call_replay import (  # noqa: E402
    ERROR_CODES,
    ReplayLedger,
    make_pack,
    replay,
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


class TestPackBuild:
    def test_pack_three_parts_complete_with_real_registry(self):
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        assert pack["schema"] == "zh-call-replay-pack/v1"
        fp = pack["input_fingerprint"]
        assert fp["utterances_digest"].startswith("sha16:")
        assert fp["normalized_digest"].startswith("sha16:")
        assert fp["registry_digest"].startswith("sha16:")
        assert pack["output"]["statuses"] == [LOOKUP["status"]]

    def test_incomplete_refused(self):
        bad = dict(CALLS[0])
        del bad["status"]
        assert make_pack([bad], REGISTRY, NORMALIZED,
                         rules_version="v1")["refused"] == "PACK_INCOMPLETE"
        assert make_pack(CALLS, REGISTRY, ["多出来的归一化（占位）", "第二条（占位）"],
                         rules_version="v1")["refused"] == "PACK_INCOMPLETE"
        assert make_pack([], REGISTRY, [],
                         rules_version="v1")["refused"] == "PACK_INCOMPLETE"


class TestReplay:
    def _pack(self):
        return make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")

    def test_same_inputs_replay_ok_real_lookup(self):
        """R2 正路：同登记册重放 lookup → REPLAY_OK（解析层复算零执行）。"""
        out = replay(self._pack(), UTTERANCES, REGISTRY, NORMALIZED,
                     lookup_fn, rules_version="v1")
        assert out["verdict"] == "REPLAY_OK"

    def test_input_drift_three_fingerprints_distinguished(self):
        """R3：三重指纹分别漂移 → INPUT_DRIFT 且漂移来源线索可区分。"""
        pack = self._pack()
        out = replay(pack, ["变了的长句（占位）"], REGISTRY, NORMALIZED,
                     lookup_fn, rules_version="v1")
        assert out["refused"] == "REPLAY_INPUT_DRIFT"
        assert "指令原文" in out["detail"]
        mutated_reg = {"entries": REGISTRY["entries"] + [
            dict(REGISTRY["entries"][0], entry_id="e-new（占位）",
                 phrase="新触发（占位）")]}
        out2 = replay(pack, UTTERANCES, mutated_reg, NORMALIZED,
                      lookup_fn, rules_version="v1")
        assert out2["refused"] == "REPLAY_INPUT_DRIFT"
        assert "登记册变" in out2["detail"]
        out3 = replay(pack, UTTERANCES, REGISTRY, ["归一化变了（占位）"],
                      lookup_fn, rules_version="v1")
        assert out3["refused"] == "REPLAY_INPUT_DRIFT"
        assert "归一化变" in out3["detail"]
        out4 = replay(pack, UTTERANCES, REGISTRY, NORMALIZED, lookup_fn,
                      rules_version="v2")
        assert out4["refused"] == "REPLAY_INPUT_DRIFT"

    def test_mismatch_first_divergence_visible(self):
        """R3：决策漂移 → MISMATCH 首分歧条显形（含候选），零静默换新解析。"""
        def drift_fn(utt, reg):
            return {"status": "ambiguous", "skill": None,
                    "candidates": [{"entry_id": "e-x（占位）",
                                    "skill": "别的包（占位）"}]}
        out = replay(self._pack(), UTTERANCES, REGISTRY, NORMALIZED,
                     drift_fn, rules_version="v1")
        assert out["verdict"] == "REPLAY_MISMATCH"
        assert out["evidence"]["first_divergence_index"] == 0
        assert out["evidence"]["got"]["status"] == "ambiguous"
        assert out["evidence"]["got"]["candidates"]


    def test_incomplete_pack_refused(self):
        out = replay({"schema": "zh-call-replay-pack/v1"}, UTTERANCES,
                     REGISTRY, NORMALIZED, lookup_fn, rules_version="v1")
        assert out["refused"] == "PACK_INCOMPLETE"


class TestLedgerAndRedline:
    def _pack(self):
        return make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")

    def test_ledger_append_only(self):
        led = ReplayLedger()
        pack = self._pack()
        led.record(pack, {"verdict": "REPLAY_OK", "evidence": None}, at=NOW)
        before = [dict(x) for x in led.entries]
        led.record(pack, {"refused": "REPLAY_INPUT_DRIFT", "evidence": None},
                   at=NOW)
        assert led.entries[0] == before[0]
        assert len(led.entries) == 2

    def test_error_codes_closed(self):
        assert set(ERROR_CODES) == {"REPLAY_INPUT_DRIFT", "REPLAY_MISMATCH",
                                    "PACK_INCOMPLETE"}

    def test_ast_zero_network_zero_subprocess(self):
        """R2 AST：解析层复算——零网络零子进程零 skill 执行导入。"""
        banned = {"urllib", "requests", "socket", "http", "subprocess"}
        src = (REPO / "scripts" / "zh_call_replay.py").read_text(
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


if __name__ == "__main__":
    pytest.main([__file__, "-q"])
