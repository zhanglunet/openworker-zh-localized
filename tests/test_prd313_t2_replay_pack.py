# -*- coding: utf-8 -*-
"""PRD-313/T2 中文 skill 调用重放包·replay-pack/v1 最小实现测试（trend #1577）。

覆盖（T1 设计 §1/§3/§4）：schema 组装与字段纪律（缺字段报错不猜、错误码封闭、
歧义消歧留痕红线）、fpv1 指纹稳定性、append-only 账本、verify_zh_replay 二值结论
（同册同指令重放必 MATCH / 换册显形 REPLAY_INPUT_MISMATCH / 重放面零写盘 /
ambiguous 重放保持待澄清不静默取候选）、与 zh_trigger_registry.lookup 出口的
端到端装订。全部占位合成零网络。
"""
import copy
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))

from zh_trigger_registry import build_registry, lookup  # noqa: E402
import replay_pack as rp  # noqa: E402

REGISTRY = build_registry()
UTTERANCE_HIT = "帮我整理一下这家客户"              # 命中 TRG-SALES-001（P1 整句精确）
UTTERANCE_MISS = "给家里的猫起个名字"


class SchemaAssemblyTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hit = lookup(REGISTRY, UTTERANCE_HIT)
        cls.pack = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, cls.hit)

    def test_pack_shape_and_registry_fingerprint(self):
        self.assertEqual(self.pack["schema_version"], "replay-pack/v1")
        self.assertEqual(self.pack["action"], "zh_skill_invoke")
        self.assertEqual(self.pack["input"]["inputs"]["utterance"], UTTERANCE_HIT)
        self.assertTrue(self.pack["input"]["inputs"]["registry_fingerprint"]
                        .startswith("fpv1:"))
        self.assertEqual(self.pack["decision"]["rules_version"],
                         REGISTRY["schema"])

    def test_hit_decision_records_skill(self):
        self.assertEqual(self.hit["status"], "hit")
        self.assertEqual(self.pack["decision"]["chosen"], self.hit["skill"])
        self.assertEqual(self.pack["output"]["result"]["status"], "hit")
        self.assertEqual(self.pack["output"]["result"]["skill"], self.hit["skill"])

    def test_fingerprint_stability_and_sensitivity(self):
        p1 = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, self.hit)
        p2 = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, self.hit)
        self.assertEqual(p1["input"]["inputs"]["registry_fingerprint"],
                         p2["input"]["inputs"]["registry_fingerprint"])
        drifted = copy.deepcopy(REGISTRY)
        drifted["entries"][0]["priority"] = "P3"
        p3 = rp.pack_from_zh_invoke(drifted, UTTERANCE_HIT,
                                    lookup(drifted, UTTERANCE_HIT))
        self.assertNotEqual(p3["input"]["inputs"]["registry_fingerprint"],
                            p1["input"]["inputs"]["registry_fingerprint"])


class AmbiguityDisciplineTests(unittest.TestCase):

    def test_ambiguous_without_disambiguation_stays_pending(self):
        """歧义不硬判（PRD-299 红线）：无人工消歧时 chosen=待人工消歧。"""
        ambiguous = {"status": "ambiguous", "skill": None,
                     "candidates": [{"entry_id": "e1", "skill": "s1",
                                     "priority": "P0", "match": "exact"}],
                     "reason": "同级候选跨技能（s1, s2）：待澄清"}
        pack = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, ambiguous)
        self.assertEqual(pack["decision"]["chosen"], "待人工消歧")
        self.assertEqual(pack["output"]["result"]["status"], "ambiguous")

    def test_disambiguation_requires_chosen_and_chosen_by(self):
        ambiguous = {"status": "ambiguous", "skill": None, "candidates": [],
                     "reason": "同级候选跨技能"}
        with self.assertRaises(rp.ReplayPackError) as ed:
            rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, ambiguous,
                                   disambiguation={"chosen": "s1"})
        self.assertEqual(ed.exception.code, "REPLAY_DECISION_FIELDS_REQUIRED")
        pack = rp.pack_from_zh_invoke(
            REGISTRY, UTTERANCE_HIT, ambiguous,
            disambiguation={"chosen": "s1", "chosen_by": "user@example.com",
                            "note": "用户当面确认"})
        self.assertEqual(pack["decision"]["chosen"], "s1")
        self.assertIn("user@example.com", pack["decision"]["why"])


class FieldDisciplineTests(unittest.TestCase):

    def test_closed_error_vocabulary(self):
        good = dict(action="zh_skill_invoke", inputs={"k": "v"},
                    decision={"chosen": "c", "why": "w", "rules_version": "v1"},
                    output={"result": "r", "key_numbers": {"n": 1}},
                    replay_command="rerun: x")
        with self.assertRaises(rp.ReplayPackError) as ei:
            rp.build_replay_pack(**{**good, "inputs": {}})
        self.assertEqual(ei.exception.code, "REPLAY_INPUT_REQUIRED")
        for drop in ("chosen", "why", "rules_version"):
            decision = {k: v for k, v in good["decision"].items() if k != drop}
            with self.assertRaises(rp.ReplayPackError) as ed:
                rp.build_replay_pack(**{**good, "decision": decision})
            self.assertEqual(ed.exception.code, "REPLAY_DECISION_FIELDS_REQUIRED")
        with self.assertRaises(ValueError):
            rp.ReplayPackError("NOT_IN_TABLE", "x")
        self.assertEqual(len(set(rp.ERROR_CODES)), len(rp.ERROR_CODES))


class LedgerTests(unittest.TestCase):

    def test_append_only_and_cold_start(self):
        pack = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT,
                                      lookup(REGISTRY, UTTERANCE_HIT))
        with tempfile.TemporaryDirectory() as tmp:
            ledger = rp.ReplayLedger(Path(tmp) / "ledger.jsonl")
            self.assertEqual(ledger.read_all(), [])
            ledger.append(pack)
            before = ledger.bytes_now()
            ledger.append(pack)
            packs = ledger.read_all()
            self.assertEqual(len(packs), 2)
            self.assertEqual(packs[0], pack)
            self.assertGreater(len(ledger.bytes_now()), len(before))


class VerifyReplayTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.hit = lookup(REGISTRY, UTTERANCE_HIT)
        cls.pack = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_HIT, cls.hit)

    def test_same_registry_replays_to_match_and_is_read_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = rp.ReplayLedger(Path(tmp) / "ledger.jsonl")
            ledger.append(self.pack)
            before = ledger.bytes_now()
            result = rp.verify_zh_replay(self.pack, REGISTRY, lookup)
            self.assertEqual(result["status"], rp.REPLAY_MATCH)
            self.assertIsNone(result["evidence"])
            self.assertEqual(ledger.bytes_now(), before)  # 重放面只读

    def test_drifted_registry_is_input_mismatch(self):
        drifted = copy.deepcopy(REGISTRY)
        drifted["entries"][0]["priority"] = "P3"
        result = rp.verify_zh_replay(self.pack, drifted, lookup)
        self.assertEqual(result["status"], rp.REPLAY_MISMATCH)
        self.assertEqual(result["evidence"]["reason"], "REPLAY_INPUT_MISMATCH")
        self.assertEqual(result["evidence"]["field"], "registry_fingerprint")

    def test_miss_replays_as_miss_not_forced_hit(self):
        pack = rp.pack_from_zh_invoke(REGISTRY, UTTERANCE_MISS,
                                      lookup(REGISTRY, UTTERANCE_MISS))
        self.assertEqual(pack["decision"]["chosen"], "miss（不硬凑）")
        result = rp.verify_zh_replay(pack, REGISTRY, lookup)
        self.assertEqual(result["status"], rp.REPLAY_MATCH)

    def test_ledger_roundtrip_replay_still_match(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = rp.ReplayLedger(Path(tmp) / "ledger.jsonl")
            ledger.append(self.pack)
            reloaded = rp.ReplayLedger(Path(tmp) / "ledger.jsonl").read_all()[0]
            result = rp.verify_zh_replay(reloaded, REGISTRY, lookup)
            self.assertEqual(result["status"], rp.REPLAY_MATCH)


if __name__ == "__main__":
    unittest.main()
