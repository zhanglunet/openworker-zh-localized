# -*- coding: utf-8 -*-
"""PRD-285/T5 验收试运行（trend #1430）：中文技能包升级快照全流程演练 + 抽查 + 本地断言 + 文档无密钥。

全链：T1 #1426（设计）→ T2 #1427（skillpack_snapshot.py 快照/还原/抽查）→
T3 #1428（spotcheck_archive.py 抽查落档+升级流程）→ T4 #1429（本地断言）→ 本验收。

红线：本地处理零网络；示例全虚构（中文占位）。
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from skillpack_snapshot import take_snapshot, restore, spot_check  # noqa: E402
from spotcheck_archive import (  # noqa: E402
    write_spotcheck_record, append_record, read_records, upgrade_flow_with_check,
)

PACK_V1 = {"skills/示例技能A/SKILL.md": "# 示例技能A v1", "skills/示例技能B/SKILL.md": "# 示例技能B v1"}
PACK_V2 = {"skills/示例技能A/SKILL.md": "# 示例技能A v2", "skills/示例技能B/SKILL.md": "# 示例技能B v2"}


class TestAcceptance(unittest.TestCase):
    def test_a1_full_flow(self):
        """全流程演练：快照→升级→抽查失败→自动回滚→回到旧包。"""
        snap = take_snapshot(PACK_V1, "2026-10-30T10:00:00Z")
        # 模拟升级后包面损坏：快照记录中 content 被改而 sha256 仍是旧值（抽查即检出）
        bad_snap = json.loads(json.dumps(snap))
        for f in bad_snap["files"].values():
            f["content"] = ""
        def restore_fn():
            return restore(snap)
        result = upgrade_flow_with_check(bad_snap, restore_fn,
                                          lambda pkg: spot_check(bad_snap), "t")
        self.assertTrue(result.get("rolled_back"))
        restored = restore(snap)
        self.assertEqual(restored, PACK_V1)

    def test_a2_upgrade_pass_no_rollback(self):
        snap = take_snapshot(PACK_V1, "t")
        # 升级后内容与快照一致（抽查全过）——升级动作把包面写到 v1 同内容
        result = upgrade_flow_with_check(snap, lambda: restore(snap),
                                          lambda pkg: spot_check(snap), "t")
        self.assertFalse(result.get("rolled_back", False))

    def test_a3_spotcheck_record(self):
        snap = take_snapshot(PACK_V1, "t")
        result = spot_check(snap)
        fp = "sha256:" + "a" * 64
        record = write_spotcheck_record(result, fp, "2026-10-30T10:05:00Z")
        self.assertEqual(record["schema"], "spotcheck-record-v1")
        self.assertEqual(record["checked"], len(PACK_V1))

    def test_a4_record_archive_roundtrip(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "spotcheck.jsonl"
            snap = take_snapshot(PACK_V1, "t")
            result = spot_check(snap)
            record = write_spotcheck_record(result, "sha256:" + "a" * 64, "t")
            append_record(record, audit)
            loaded = read_records(audit)
        self.assertEqual(len(loaded), 1)

    def test_a5_fingerprint_verified_on_restore(self):
        snap = take_snapshot(PACK_V1, "t")
        tampered = json.loads(json.dumps(snap))
        tampered["fingerprint"] = "deadbeef"
        with self.assertRaises(Exception):
            restore(tampered)

    def test_a6_local_only(self):
        for name in ("skillpack_snapshot.py", "spotcheck_archive.py"):
            src = (Path(__file__).resolve().parents[1] / "scripts" / name).read_text(encoding="utf-8")
            for banned in ("requests", "urllib", "socket", "http.client"):
                self.assertNotIn(banned, src)

    def test_a7_secrets_scan(self):
        for name in ("skillpack_snapshot.py", "spotcheck_archive.py"):
            src = (Path(__file__).resolve().parents[1] / "scripts" / name).read_text(encoding="utf-8")
            self.assertNotIn("sk-placeholder0123456789", src)
            self.assertNotIn("AK" + "IA", src)

    def test_a8_deterministic(self):
        s1 = take_snapshot(PACK_V1, "t")
        s2 = take_snapshot(PACK_V1, "t")
        self.assertEqual(json.dumps(s1, sort_keys=True), json.dumps(s2, sort_keys=True))


if __name__ == "__main__":
    unittest.main()
