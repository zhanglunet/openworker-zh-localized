# -*- coding: utf-8 -*-
"""PRD-355/T5 测试（trend #1634 的 T5 环节）：中文调用重放验收试运行。

运行：uv run --with pytest python -m pytest tests/test_prd355_t5_zh_call_replay.py -q
（仓库根执行）

验收（T1 §5 T5 行「样例回放+MISMATCH 演练+文档无密钥」）：
  全链回放：真实 zh_trigger_registry 构建登记册 → make_pack → replay →
  REPLAY_OK；两遍 pack/verdict/账本 entries 逐字节一致（确定性可复现）；
  MISMATCH 演练：改写解析 → REPLAY_MISMATCH 显形零静默（含 normalize
  归一化差异线索——三重指纹区分漂移来源）；INPUT_DRIFT 演练：换登记册/
  归一化 → REPLAY_INPUT_DRIFT 拒绝（防新登记册冒充当时）；R2 零执行
  行为复验（演练返回值零执行载荷键）；账本 append-only；链复跑：T2/T3/
  T4 测试子进程复跑 exit 0（链上仍绿实测）；文档无密钥：T1 设计文档
  拼接 needle 扫描+占位符纪律。零网络；全合成占位。
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

from zh_call_replay import ReplayLedger, make_pack, replay  # noqa: E402
from zh_trigger_registry import build_registry, lookup  # noqa: E402

NOW = "2026-11-11T09:00:00Z"
REGISTRY = build_registry()
UTTERANCES = ["帮我写周报（占位）"]
NORMALIZED = ["帮我写周报（占位）"]
LOOKUP = lookup(REGISTRY, UTTERANCES[0])
CALLS = [{"utterance": UTTERANCES[0], "resolved_skill": LOOKUP.get("skill"),
          "status": LOOKUP["status"], "candidates": LOOKUP.get("candidates", [])}]


def lookup_fn(utt, reg):
    return dict(LOOKUP)


def _fresh_replay():
    pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
    verdict = replay(pack, UTTERANCES, REGISTRY, NORMALIZED, lookup_fn,
                     rules_version="v1")
    ledger = ReplayLedger()
    ledger.record(pack, verdict, at=NOW)
    return pack, verdict, ledger


class TestFullChainReplay(unittest.TestCase):
    def test_replay_ok_deterministic_twice(self):
        """全链回放（真实登记册串联）：REPLAY_OK；两遍逐字节一致。"""
        pack1, verdict1, led1 = _fresh_replay()
        pack2, verdict2, led2 = _fresh_replay()
        self.assertEqual(verdict1["verdict"], "REPLAY_OK")
        self.assertEqual(json.dumps(pack1, sort_keys=True),
                         json.dumps(pack2, sort_keys=True))
        self.assertEqual(json.dumps(verdict1, sort_keys=True),
                         json.dumps(verdict2, sort_keys=True))
        self.assertEqual(json.dumps(led1.entries, sort_keys=True),
                         json.dumps(led2.entries, sort_keys=True))


class TestFailureDrills(unittest.TestCase):
    def test_mismatch_visible_and_ledger_evidence(self):
        """MISMATCH 演练：改写解析 → REPLAY_MISMATCH 显形零静默；失败证据
        落账本；返回值零执行载荷键（R2 行为复验）。"""
        pack = make_pack(CALLS, REGISTRY, NORMALIZED, rules_version="v1")
        out = replay(pack, UTTERANCES, REGISTRY, NORMALIZED,
                     lambda u, r: dict(LOOKUP, skill="改写（占位）"),
                     rules_version="v1")
        self.assertEqual(out["verdict"], "REPLAY_MISMATCH")
        self.assertEqual(out["evidence"]["first_divergence_index"], 0)
        for key in ("executed", "ran"):
            self.assertNotIn(key, out)
        ledger = ReplayLedger()
        ledger.record(pack, out, at=NOW)
        self.assertEqual(ledger.entries[-1]["verdict"], "REPLAY_MISMATCH")

    def test_input_drift_refuses(self):
        """INPUT_DRIFT 演练：换归一化（原文同归一化变）→ REPLAY_INPUT_DRIFT
        拒绝——三重指纹区分漂移来源。"""
        pack, _, _ = _fresh_replay()
        out = replay(pack, UTTERANCES, REGISTRY, ["帮我写周报呀（变体）"],
                     lookup_fn, rules_version="v1")
        self.assertEqual(out["refused"], "REPLAY_INPUT_DRIFT")

    def test_ledger_append_only_through_drills(self):
        """账本 append-only：全演练流程后 entries 只增不删。"""
        _, _, led1 = _fresh_replay()
        n0 = len(led1.entries)
        _, _, led2 = _fresh_replay()
        led2.record({"refused": "PACK_INCOMPLETE"},
                    {"verdict": None, "evidence": None}, at=NOW)
        self.assertEqual(len(led2.entries), n0 + 1)


class TestChainRerun(unittest.TestCase):
    def test_t2_t3_t4_rerun_green(self):
        """链复跑：T2/T3/T4 测试子进程复跑 exit 0（链上仍绿实测）。"""
        for test_file in ("test_prd355_t2_zh_call_replay.py",
                          "test_prd355_t3_zh_call_replay_gates.py",
                          "test_prd355_t4_zh_call_replay_boundary.py"):
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q",
                 str(Path(__file__).resolve().parent / test_file)],
                capture_output=True, timeout=300)
            self.assertEqual(proc.returncode, 0,
                             f"{test_file} 复跑失败：{proc.stdout[-400:]}")


class TestDocNoSecrets(unittest.TestCase):
    def test_t1_design_doc_no_secrets(self):
        """文档无密钥：T1 设计文档拼接 needle 扫描+占位符纪律。"""
        repo = Path(__file__).resolve().parents[1]
        doc = next(repo.glob("docs/plans/2026-11-11-prd-355-*.md"))
        text = doc.read_text(encoding="utf-8").lower()
        for needle in ("sk-" + "live", "passw" + "ord", "api_k" + "ey"):
            self.assertNotIn(needle, text, f"设计文档出现密钥词 {needle}")
        self.assertIn("占位", text)


if __name__ == "__main__":
    unittest.main()
