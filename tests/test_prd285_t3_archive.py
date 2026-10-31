# -*- coding: utf-8 -*-
"""PRD-285/T3 自测（trend #1428）：升级后抽查记录正式化与落档。

运行：.venv/bin/python -m pytest tests/test_prd285_t3_archive.py -q

覆盖（T3 验收，≥6 例）：
  记录 schema 字段齐全（固定六字段、计数一致、datetime 归一、多余键忽略）
  记录校验拒绝（非 dict / 缺计数 / 计数不一致 / 负数 / 指纹形态 / 空时间戳）
  append 后可读（JSONL 一行一记录、roundtrip 相等、父目录自动创建）
  全量读取（多记录顺序保持、追加不覆盖、缺失/空文件、坏行带行号拒绝）
  append 拒绝非记录（schema 不符 / 缺字段 / 不可序列化，文件不被污染）
  升级抽查全过不回滚（failed=0 → restore_fn 不被调用）
  抽查失败自动回滚（failed>0 → restore_fn 恰好一次、返回值透传）
  与 T2 端到端（take_snapshot → 抽查检出损坏 → ssp.restore 自动回滚旧包 → 落档读回）
  确定性（同输入同记录同 JSONL 字节；append-only 同记录同行）
"""
import copy
import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent


def _load(name, relpath):
    spec = importlib.util.spec_from_file_location(name, REPO / relpath)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ssp = _load("skillpack_snapshot", "scripts/skillpack_snapshot.py")   # T2
sca = _load("spotcheck_archive", "scripts/spotcheck_archive.py")     # T3

T0 = "2026-10-29T09:00:00+08:00"
T1 = "2026-10-29T09:05:00+08:00"
FP = "sha256:" + "a1b2c3d4" * 8


def sample_pack():
    """虚构中文技能包（与 T2 测试同源的占位样例）。"""
    return {
        "zh-sales-lead-brief/SKILL.md": (
            "---\nname: zh-sales-lead-brief\n"
            "description: 每日销售线索简报（虚构示例技能）\n---\n\n"
            "按触发词「销售简报」调用本技能。\n"
        ),
        "zh-sales-lead-brief/references/playbook.md": (
            "# 跟进手册（虚构示例）\n\n第一步：占位步骤。\n"
        ),
    }


class WriteSpotcheckRecordTest(unittest.TestCase):
    # 1. 记录 schema 字段齐全
    def test_record_schema_fields(self):
        record = sca.write_spotcheck_record(
            {"checked": 3, "passed": 2, "failed": 1, "failed_paths": ["x"], "sample_paths": ["x", "y", "z"]},
            FP, T0,
        )
        self.assertEqual(record["schema"], "spotcheck-record-v1")
        self.assertEqual(record["snapshot_fingerprint"], FP)
        self.assertEqual(record["checked"], 3)
        self.assertEqual(record["passed"], 2)
        self.assertEqual(record["failed"], 1)
        self.assertEqual(record["at"], T0)
        self.assertEqual(set(record), {"schema", "snapshot_fingerprint", "checked", "passed", "failed", "at"})
        self.assertTrue(json.dumps(record, ensure_ascii=False))  # 机读可序列化
        # datetime 归一为 isoformat；多余键忽略
        from datetime import datetime as dt
        record2 = sca.write_spotcheck_record(
            {"checked": 1, "passed": 1, "failed": 0}, FP, dt(2026, 10, 29, 9, 0, 0))
        self.assertEqual(record2["at"], "2026-10-29T09:00:00")

    # 2. 记录校验拒绝（fail-close）
    def test_record_validation_rejects(self):
        with self.assertRaises(sca.SpotcheckArchiveError):
            sca.write_spotcheck_record("not-a-dict", FP, T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # 缺 failed
            sca.write_spotcheck_record({"checked": 1, "passed": 1}, FP, T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # 计数不一致
            sca.write_spotcheck_record({"checked": 3, "passed": 1, "failed": 1}, FP, T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # 负数
            sca.write_spotcheck_record({"checked": 1, "passed": 2, "failed": -1}, FP, T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # bool 不是整数
            sca.write_spotcheck_record({"checked": True, "passed": True, "failed": 0}, FP, T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # 指纹形态（无前缀）
            sca.write_spotcheck_record({"checked": 0, "passed": 0, "failed": 0}, "deadbeef", T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # 指纹十六进制段不足 64
            sca.write_spotcheck_record({"checked": 0, "passed": 0, "failed": 0}, "sha256:abcd", T0)
        with self.assertRaises(sca.SpotcheckArchiveError):  # 空时间戳
            sca.write_spotcheck_record({"checked": 0, "passed": 0, "failed": 0}, FP, "  ")


class AppendReadTest(unittest.TestCase):
    # 3. append 后可读（roundtrip + 父目录自动创建）
    def test_append_roundtrip_and_parent_dirs(self):
        record = sca.write_spotcheck_record({"checked": 2, "passed": 2, "failed": 0}, FP, T0)
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "nested" / "dir" / "audit.jsonl"   # 父目录不存在
            returned = sca.append_record(record, audit)
            self.assertEqual(returned, record)
            self.assertTrue(audit.exists())
            text = audit.read_text(encoding="utf-8")
            self.assertEqual(len(text.splitlines()), 1)            # 一行一记录
            self.assertEqual(json.loads(text), record)             # JSONL 可解析
            self.assertEqual(sca.read_records(audit), [record])    # 读回相等

    # 4. 全量读取：多记录顺序保持、追加不覆盖、缺失/空文件、坏行拒绝
    def test_read_full_order_and_edges(self):
        records = [
            sca.write_spotcheck_record({"checked": 1, "passed": 1, "failed": 0}, FP, T0),
            sca.write_spotcheck_record({"checked": 3, "passed": 2, "failed": 1}, FP, T1),
            sca.write_spotcheck_record({"checked": 0, "passed": 0, "failed": 0}, FP, "2026-10-29T10:00:00+08:00"),
        ]
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.jsonl"
            self.assertEqual(sca.read_records(audit), [])          # 缺失文件 → 空
            audit.write_text("", encoding="utf-8")
            self.assertEqual(sca.read_records(audit), [])          # 空文件 → 空
            for record in records:
                sca.append_record(record, audit)                   # 追加不覆盖
            self.assertEqual(sca.read_records(audit), records)     # 全量、顺序保持
            audit.write_text("{broken json\n", encoding="utf-8")
            with self.assertRaises(sca.SpotcheckArchiveError) as ctx:
                sca.read_records(audit)
            self.assertIn("1", str(ctx.exception))                 # 坏行带行号，拒绝静默跳过

    # 5. append 拒绝非记录，文件不被污染
    def test_append_rejects_bad_record(self):
        good = sca.write_spotcheck_record({"checked": 1, "passed": 0, "failed": 1}, FP, T0)
        bad_cases = [
            "not-a-dict",
            {"schema": "rollback-record-v1", "at": T0},            # schema 不符
            {"schema": "spotcheck-record-v1", "at": T0},           # 缺字段
        ]
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.jsonl"
            sca.append_record(good, audit)
            for bad in bad_cases:
                with self.assertRaises(sca.SpotcheckArchiveError):
                    sca.append_record(bad, audit)
            self.assertEqual(sca.read_records(audit), [good])      # 坏记录未污染存档
            with self.assertRaises(sca.SpotcheckArchiveError):     # 不可序列化
                sca.append_record({**good, "checked": object()}, audit)


class UpgradeFlowTest(unittest.TestCase):
    def setUp(self):
        ssp.clear_slot()

    def tearDown(self):
        ssp.clear_slot()

    # 6. 升级抽查全过不回滚
    def test_flow_all_pass_no_rollback(self):
        snap = {"fingerprint": FP}
        calls = []
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.jsonl"
            out = sca.upgrade_flow_with_check(
                snap,
                restore_fn=lambda: calls.append(1),                # 不应被调用
                check_fn=lambda _s: {"checked": 2, "passed": 2, "failed": 0},
                at=T1,
                audit_path=audit,
            )
            self.assertEqual(sca.read_records(audit), [out["record"]])  # 记录仍落档
        self.assertFalse(out["rolled_back"])
        self.assertIsNone(out["restored"])
        self.assertEqual(calls, [])
        self.assertEqual(out["record"]["failed"], 0)
        self.assertEqual(out["record"]["snapshot_fingerprint"], FP)

    # 7. 抽查失败自动回滚（failed>0 → restore 恰好一次）
    def test_flow_failure_auto_rollback(self):
        snap = {"fingerprint": FP}
        calls = []
        def restore_fn():
            calls.append(1)
            return {"restored": "old-pack"}
        out = sca.upgrade_flow_with_check(
            snap,
            restore_fn=restore_fn,
            check_fn=lambda _s: {"checked": 3, "passed": 1, "failed": 2},
            at=T1,
        )
        self.assertTrue(out["rolled_back"])
        self.assertEqual(len(calls), 1)                            # 恰好回滚一次
        self.assertEqual(out["restored"], {"restored": "old-pack"})
        self.assertEqual(out["record"]["failed"], 2)

    # 8. 与 T2 端到端：抽查检出损坏 → ssp.restore 自动回滚旧包 → 落档读回
    def test_flow_end_to_end_with_t2_spotcheck(self):
        pack = sample_pack()
        snap = ssp.take_snapshot(pack, T0)
        broken = copy.deepcopy(snap)                               # 模拟升级后的坏包面
        path = "zh-sales-lead-brief/SKILL.md"
        broken["files"][path]["content"] = "被覆盖的坏内容\n"        # 与记录 sha256 不符
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.jsonl"
            out = sca.upgrade_flow_with_check(
                snap,
                restore_fn=ssp.restore,                            # T2 单槽回滚：返回旧包
                check_fn=lambda _s: ssp.spot_check(broken),        # T2 抽查：检出损坏
                at=T1,
                audit_path=audit,
            )
            (record,) = sca.read_records(audit)
            self.assertEqual(record, out["record"])
        self.assertTrue(out["rolled_back"])
        self.assertEqual(out["restored"], pack)                    # 回滚返回旧包（与 pack_dir 同形）
        self.assertEqual(out["record"]["snapshot_fingerprint"], snap["fingerprint"])
        self.assertEqual(out["record"]["failed"], 1)
        # 回滚可再回滚：单槽未被顶替
        self.assertEqual(ssp.restore(), pack)

    # 9. flow 入参与记录校验的 fail-close
    def test_flow_input_validation(self):
        with self.assertRaises(sca.SpotcheckArchiveError):         # 快照无 fingerprint
            sca.upgrade_flow_with_check({}, lambda: None, lambda _s: {"checked": 0, "passed": 0, "failed": 0}, T1)
        with self.assertRaises(sca.SpotcheckArchiveError):         # check_fn 不可调用
            sca.upgrade_flow_with_check({"fingerprint": FP}, lambda: None, "nope", T1)
        with self.assertRaises(ssp.SkillpackSnapshotError):        # check_fn 抛错原样上抛（不吞）
            sca.upgrade_flow_with_check(
                {"fingerprint": FP}, lambda: None,
                lambda _s: (_ for _ in ()).throw(ssp.SkillpackSnapshotError("快照结构缺损")), T1)


class DeterminismTest(unittest.TestCase):
    # 10. 确定性：同输入同记录同 JSONL 字节
    def test_determinism(self):
        result = {"checked": 2, "passed": 2, "failed": 0}
        r1 = sca.write_spotcheck_record(result, FP, T0)
        r2 = sca.write_spotcheck_record(dict(result), FP, T0)
        self.assertEqual(r1, r2)
        self.assertEqual(
            json.dumps(r1, sort_keys=True, ensure_ascii=False),
            json.dumps(r2, sort_keys=True, ensure_ascii=False),
        )
        out1 = sca.upgrade_flow_with_check(
            {"fingerprint": FP}, lambda: None, lambda _s: dict(result), T1)
        out2 = sca.upgrade_flow_with_check(
            {"fingerprint": FP}, lambda: None, lambda _s: dict(result), T1)
        self.assertEqual(out1["record"], out2["record"])
        self.assertFalse(out1["rolled_back"])
        with tempfile.TemporaryDirectory() as tmp:
            audit = Path(tmp) / "audit.jsonl"
            sca.append_record(r1, audit)
            sca.append_record(r2, audit)
            lines = audit.read_text(encoding="utf-8").splitlines()
            self.assertEqual(lines[0], lines[1])                   # 同记录必同字节（append-only 不去重）
            self.assertEqual(sca.read_records(audit), [r1, r2])


if __name__ == "__main__":
    unittest.main()
