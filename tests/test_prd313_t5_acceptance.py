# -*- coding: utf-8 -*-
"""PRD-313/T5 验收试运行（trend #1580）。

- 全链路两遍：动作出口 → 装订重放包 → append-only 账本 → verify 重放 →
  replay_gate 过闸；两遍产物（pack 指纹/verify/gate）逐字节一致；
- 红线终检：        blobs, gate, _ = _chain()
        self.assertTrue(gate["allow"])
        # 歧义不硬判：miss/待人工消歧的 chosen 不携带静默候选
        self.assertNotIn("auto_disambiguate", json.dumps(blobs, ensure_ascii=False))；
- 文档无密钥：T1 设计文档与 replay_pack/测试 私钥/密钥模式零命中。
"""
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

sys.path.insert(0, str(REPO / "scripts"))
import replay_pack as rp  # noqa: E402

T1_DOCS = sorted(Path(str(REPO)).glob("docs/**/*prd-313*"))
SECRET_PATTERNS = [
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----", r"AKIA[0-9A-Z]{16}",
    r"ghp_[A-Za-z0-9]{20,}",
    r"sk-[A-Za-z0-9]{20,}",
    r"(?i)password\s*[:=]\s*\S{6,}", r"(?i)(api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*\S{8,}",
]

from zh_trigger_registry import lookup  # noqa: E402
import replay_pack as rp  # noqa: E402
from test_prd313_t2_replay_pack import REGISTRY, UTTERANCE_HIT  # noqa: E402


def _chain():
    hit = lookup(REGISTRY, UTTERANCE_HIT)
    pack = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, hit)
    with tempfile.TemporaryDirectory() as tmp:
        ledger = rp.ReplayLedger(Path(tmp) / "ledger.jsonl")
        ledger.append(pack)
        reloaded = rp.ReplayLedger(Path(tmp) / "ledger.jsonl").read_all()[0]
        verify = rp.verify_zh_replay(reloaded, REGISTRY, lookup)
    gate = rp.replay_gate(verify)
    blobs = {"pack_fp": pack["input"]["snapshot_fingerprint"],
             "pack_output": rp.canonical_bytes(pack["output"]).decode("utf-8"),
             "verify": rp.canonical_bytes(verify).decode("utf-8"), "gate": rp.canonical_bytes(gate).decode("utf-8")}
    return blobs, gate, ledger

class AcceptanceTests(unittest.TestCase):

    def test_full_chain_replay_twice_byte_identical(self):
        blobs1, gate1, _ = _chain()
        blobs2, gate2, _ = _chain()
        for k in blobs1:
            self.assertEqual(blobs1[k], blobs2[k], f"两遍不一致：{k}")
        self.assertEqual(gate1, gate2)
        self.assertTrue(gate1["allow"])  # 全链路过闸

    def test_gate_refusal_leaves_ledger_untouched(self):
        blobs, gate, ledger = _chain()
        before = ledger.bytes_now()
        verdict = rp.replay_gate({"status": "MISMATCH", "evidence": {"x": 1}})
        self.assertFalse(verdict["allow"])
        self.assertEqual(ledger.bytes_now(), before)  # 拒绝零写盘

    def test_redline_final_check(self):
        blobs, gate, _ = _chain()
        self.assertTrue(gate["allow"])
        # 歧义不硬判：miss/待人工消歧的 chosen 不携带静默候选
        self.assertNotIn("auto_disambiguate", json.dumps(blobs, ensure_ascii=False))

    def test_docs_and_code_no_secrets(self):
        targets = list(T1_DOCS) + [Path("scripts/replay_pack.py")] + \
            sorted(Path(str(REPO)).glob("tests/test_prd313_*.py"))
        self.assertTrue(targets, "验收扫描目标为空（doc/模块/测试至少其一）")
        patterns = [re.compile(p) for p in SECRET_PATTERNS]
        for f in targets:
            text = f.read_text(encoding="utf-8")
            for pat in patterns:
                self.assertIsNone(pat.search(text),
                                  f"{f.name} 命中密钥模式 {pat.pattern}")


if __name__ == "__main__":
    unittest.main()
