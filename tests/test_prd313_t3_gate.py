# -*- coding: utf-8 -*-
"""PRD-313/T3 重放校验闸门测试（trend #1578）。

覆盖（T1 §3 + T3 口径）：闸门一票否决——MATCH 放行；MISMATCH/被篡改产物/未知
status/缺产物 一律 REPLAY_GATE_REFUSED；require_gate 异常形态；闸门拒绝时
调用方不得使用账本/重放数据（决策面模拟：拒绝路径走人工，零静默给新数）；
错误码封闭（词表含 GATE_REFUSED 且无重复）。
sys.path.insert(0, str(REPO / "scripts"))
import replay_pack as rp
"""
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

import replay_pack as rp  # noqa: E402

def _verify(status="MATCH", *, evidence=None, fp="fpv1:abc"):
    return {"action": "x", "input_snapshot_fingerprint": fp,
            "status": status, "expect": "byte-identical",
            "fingerprint_algo": "fpv1", "evidence": evidence}


class GateVerdictTests(unittest.TestCase):

    def test_match_passes(self):
        v = rp.replay_gate(_verify("MATCH"))
        self.assertTrue(v["allow"])
        self.assertIsNone(v["code"])

    def test_mismatch_refused_with_evidence(self):
        ev = {"ledger": 1, "rerun": 2}
        v = rp.replay_gate(_verify("MISMATCH", evidence=ev))
        self.assertFalse(v["allow"])
        self.assertEqual(v["code"], "REPLAY_GATE_REFUSED")
        self.assertEqual(v["evidence"], ev)

    def test_missing_or_tampered_product_refused(self):
        self.assertFalse(rp.replay_gate(None)["allow"])
        self.assertFalse(rp.replay_gate({})["allow"])
        self.assertFalse(rp.replay_gate(_verify("NOT_RUN"))["allow"])
        self.assertFalse(rp.replay_gate({"status": 123})["allow"])
        self.assertFalse(rp.replay_gate({"status": None})["allow"])
        for v in (rp.replay_gate(None), rp.replay_gate({})):
            self.assertEqual(v["code"], "REPLAY_GATE_REFUSED")

    def test_require_gate_raises_and_passes(self):
        with self.assertRaises(rp.ReplayPackError) as eg:
            rp.require_gate(_verify("MISMATCH", evidence={"x": 1}))
        self.assertEqual(eg.exception.code, "REPLAY_GATE_REFUSED")
        self.assertEqual(rp.require_gate(_verify("MATCH"))["status"], "MATCH")

    def test_closed_vocabulary_includes_gate_code(self):
        self.assertIn("REPLAY_GATE_REFUSED", rp.ERROR_CODES)
        self.assertEqual(len(set(rp.ERROR_CODES)), len(rp.ERROR_CODES))


class DecisionSurfaceTests(unittest.TestCase):

    def test_refused_path_goes_to_manual_not_silent_new_data(self):
        ev = {"ledger": ["旧结论"], "rerun": ["新数据"]}
        verdict = rp.replay_gate(_verify("MISMATCH", evidence=ev))
        consumed = []
        if verdict["allow"]:
            consumed.append(verdict)
        consumed.append({"route": "manual", "evidence": verdict.get("evidence")})
        self.assertEqual(consumed, [{"route": "manual", "evidence": ev}])

    def test_allowed_path_consumes_result(self):
        verdict = rp.replay_gate(_verify("MATCH"))
        consumed = []
        if verdict["allow"]:
            consumed.append({"route": "use_result"})
        self.assertEqual(consumed, [{"route": "use_result"}])


if __name__ == "__main__":
    unittest.main()
