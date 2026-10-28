# -*- coding: utf-8 -*-
"""PRD-285/T2 自测（trend #1427）：中文技能包升级——快照存储与回滚最小实现。

运行：.venv/bin/python -m pytest tests/test_prd285_t2_snapshot.py -q

覆盖（T2 验收，≥8 例）：
  快照字段齐全（schema/taken_at/files/fingerprint）+ 深拷贝隔离
  指纹确定性（同输入同 taken_at → 同指纹；改文件即变）
  还原：显式快照与单槽 restore 均还原旧包内容（与 pack_dir 同形）
  指纹篡改：改文件内容/改记录指纹/结构缺损 → FingerprintMismatch
  抽查全过：≤5 全查零失败
  抽查失败检出：内容损坏/样本路径缺失 → failed 精确定位
  抽样策略：>5 字典序抽 3（确定性、无随机性）；sample_paths 显式指定生效
  审计事件（upgraded/rolled_back/spot_checked）：校验+追加+导出可序列化
  单槽：新快照顶替旧快照（restore() 只回上一版）；空槽 restore 拒绝
  全链零网络；示例全中文虚构（zh-sales-lead-brief 为 PRD-183 规划的虚构示例名）
"""
import copy
import importlib.util
import json
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_SCRIPT = REPO / "scripts" / "skillpack_snapshot.py"
_spec = importlib.util.spec_from_file_location("skillpack_snapshot", _SCRIPT)
ssp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ssp)

T0 = "2026-10-29T09:00:00+08:00"
T1 = "2026-10-29T14:30:00+08:00"


def sample_pack():
    """虚构中文技能包（folder-is-truth 的内存形态：{相对路径: 文件内容}）。"""
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


def sample_event(**overrides):
    event = {
        "event": "spe-000000000001",
        "change_type": "upgraded",
        "at": T0,
        "actor": "operator",
        "summary": "中文技能包升级应用（占位安装会话 ref-0001）",
    }
    event.update(overrides)
    return event


class SkillpackSnapshotTest(unittest.TestCase):
    def setUp(self):
        ssp.clear_slot()

    def tearDown(self):
        ssp.clear_slot()

    # 1. 快照字段与深拷贝隔离
    def test_snapshot_fields_and_deep_copy(self):
        pack = sample_pack()
        snap = ssp.take_snapshot(pack, T0)
        self.assertEqual(snap["schema"], "skillpack-snapshot-v1")
        self.assertEqual(snap["taken_at"], T0)
        self.assertEqual(set(snap), {"schema", "taken_at", "files", "fingerprint"})
        self.assertTrue(snap["fingerprint"].startswith("sha256:"))
        self.assertEqual(set(snap["files"]), set(pack))
        # files 存 {content, sha256, bytes} 记录
        record = snap["files"]["zh-sales-lead-brief/SKILL.md"]
        self.assertEqual(record["content"], pack["zh-sales-lead-brief/SKILL.md"])
        self.assertEqual(record["bytes"], len(pack["zh-sales-lead-brief/SKILL.md"].encode("utf-8")))
        # 调用方随后改动原 pack，不污染快照（深拷贝）
        original_skill_md = snap["files"]["zh-sales-lead-brief/SKILL.md"]["content"]
        pack["zh-sales-lead-brief/SKILL.md"] = "升级后的新内容\n"
        self.assertEqual(snap["files"]["zh-sales-lead-brief/SKILL.md"]["content"], original_skill_md)
        # 快照入槽为深拷贝：改动返回的快照不污染槽
        snap["files"]["zh-sales-lead-brief/SKILL.md"]["content"] = "篡改\n"
        self.assertNotIn("篡改", ssp.restore()["zh-sales-lead-brief/SKILL.md"])

    # 2. 指纹确定性
    def test_fingerprint_deterministic_and_sensitive(self):
        t = "2026-10-29T09:00:00+08:00"
        s1 = ssp.take_snapshot(sample_pack(), t)
        s2 = ssp.take_snapshot(sample_pack(), t)
        self.assertEqual(s1["fingerprint"], s2["fingerprint"])
        # 改任一文件内容 → 指纹变
        pack_b = sample_pack()
        pack_b["zh-sales-lead-brief/references/playbook.md"] = "# 跟进手册（升级版，占位）\n"
        s3 = ssp.take_snapshot(pack_b, t)
        self.assertNotEqual(s3["fingerprint"], s1["fingerprint"])
        # 文件名不同、内容相同 → 指纹也不同（清单含路径）
        pack_c = {"zh-other-brief/SKILL.md": list(sample_pack().values())[0]}
        s4 = ssp.take_snapshot(pack_c, t)
        self.assertNotEqual(s4["fingerprint"], s1["fingerprint"])

    # 3. 还原
    def test_restore_roundtrip(self):
        pack = sample_pack()
        snap = ssp.take_snapshot(pack, T0)
        restored = ssp.restore(snap)
        self.assertEqual(restored, pack)
        # 还原值与快照隔离：改动不影响快照，可重复还原
        restored["zh-sales-lead-brief/SKILL.md"] = "又被改了\n"
        self.assertEqual(ssp.restore(snap), pack)
        # 单槽路径：restore() 还原最近一张
        pack_b = sample_pack()
        pack_b["zh-sales-lead-brief/SKILL.md"] = "---\nname: zh-sales-lead-brief\n---\n升级版（占位）\n"
        ssp.take_snapshot(pack_b, T1)
        self.assertEqual(ssp.restore(), pack_b)
        # 显式还原旧快照仍可（审计追溯通道）
        self.assertEqual(ssp.restore(snap), sample_pack())

    # 4. 指纹篡改抛错
    def test_tampered_fingerprint_raises(self):
        snap = ssp.take_snapshot(sample_pack(), T0)
        # 篡改文件内容 → 重算指纹不符
        bad_content = copy.deepcopy(snap)
        bad_content["files"]["zh-sales-lead-brief/SKILL.md"]["content"] = "被覆盖的新版（占位）\n"
        with self.assertRaises(ssp.FingerprintMismatch):
            ssp.restore(bad_content)
        # 篡改记录的指纹本身
        bad_record = copy.deepcopy(snap)
        bad_record["fingerprint"] = "sha256:" + "0" * 64
        with self.assertRaises(ssp.FingerprintMismatch):
            ssp.restore(bad_record)
        # 结构缺损（files 缺失）拒绝还原
        bad_shape = copy.deepcopy(snap)
        del bad_shape["files"]
        with self.assertRaises(ssp.FingerprintMismatch):
            ssp.restore(bad_shape)
        # schema 不符拒绝
        bad_schema = copy.deepcopy(snap)
        bad_schema["schema"] = "skillpack-snapshot-v2"
        with self.assertRaises(ssp.SkillpackSnapshotError):
            ssp.restore(bad_schema)

    # 5. 抽查全过（≤5 全查）
    def test_spot_check_all_pass(self):
        snap = ssp.take_snapshot(sample_pack(), T0)
        self.assertEqual(len(snap["files"]), 2)
        report = ssp.spot_check(snap)
        self.assertEqual(report["checked"], 2)  # ≤5 全查
        self.assertEqual(report["passed"], 2)
        self.assertEqual(report["failed"], 0)
        self.assertEqual(report["failed_paths"], [])

    # 6. 抽查失败检出
    def test_spot_check_detects_failures(self):
        snap = ssp.take_snapshot(sample_pack(), T0)
        # 升级后个别文件被覆盖（只改 content、清单记录未同步）→ 抽查精确定位
        corrupted = copy.deepcopy(snap)
        corrupted["files"]["zh-sales-lead-brief/SKILL.md"]["content"] = "损坏的内容（占位）\n"
        report = ssp.spot_check(corrupted)
        self.assertEqual(report["checked"], 2)
        self.assertEqual(report["passed"], 1)
        self.assertEqual(report["failed"], 1)
        self.assertEqual(report["failed_paths"], ["zh-sales-lead-brief/SKILL.md"])
        # 显式样本路径含快照外路径 → 该样本计 failed（缺失）
        report2 = ssp.spot_check(snap, sample_paths=[
            "zh-sales-lead-brief/SKILL.md", "zh-sales-lead-brief/不存在.md"])
        self.assertEqual(report2["checked"], 2)
        self.assertEqual(report2["failed"], 1)
        self.assertEqual(report2["failed_paths"], ["zh-sales-lead-brief/不存在.md"])

    # 7. 抽样策略（>5 字典序抽 3，确定性）
    def test_spot_check_sampling_strategy(self):
        pack = {f"zh-demo/f{i:02d}.md": f"虚构文件 {i}\n" for i in range(7)}
        pack["zh-demo/SKILL.md"] = "---\nname: zh-demo\n---\n占位\n"
        snap = ssp.take_snapshot(pack, T0)
        self.assertGreater(len(snap["files"]), ssp.SPOT_CHECK_ALL_MAX)
        report = ssp.spot_check(snap)  # 缺省：字典序前 3
        self.assertEqual(report["checked"], ssp.SPOT_CHECK_DEFAULT_N)
        self.assertEqual(report["sample_paths"], sorted(pack)[:3])
        self.assertEqual(report["passed"], 3)
        self.assertEqual(report["failed"], 0)
        # 两次抽查结果一致（确定性抽样，可复现、可对账）
        self.assertEqual(ssp.spot_check(snap), report)
        # 显式 max_n 生效
        self.assertEqual(ssp.spot_check(snap, max_n=5)["checked"], 5)
        # 显式 sample_paths 生效
        picked = ssp.spot_check(snap, sample_paths=["zh-demo/SKILL.md"])
        self.assertEqual(picked["sample_paths"], ["zh-demo/SKILL.md"])

    # 8. 审计事件（upgraded/rolled_back/spot_checked）可序列化
    def test_audit_events_serializable(self):
        events: list = []
        ssp.audit_append(events, sample_event())
        ssp.audit_append(events, sample_event(event="spe-000000000002", change_type="spot_checked",
                                              at=T0, summary="升级后抽查通过（2/2，占位）"))
        ssp.audit_append(events, sample_event(event="spe-000000000003", change_type="rolled_back",
                                              at=T1, summary="升级后触发例命中失败，回旧包（占位）"))
        self.assertEqual([e["change_type"] for e in events],
                         ["upgraded", "spot_checked", "rolled_back"])
        # 未知 change_type 拒绝
        with self.assertRaises(ssp.AuditEventError):
            ssp.audit_append(events, sample_event(event="spe-000000000004", change_type="hacked"))
        # 同 event id 重放拒绝（append-only）
        with self.assertRaises(ssp.AuditEventError):
            ssp.audit_append(events, sample_event(event="spe-000000000001"))
        # 缺必填字段拒绝
        with self.assertRaises(ssp.AuditEventError):
            ssp.audit_append(events, {"change_type": "upgraded"})
        # 缺省 event id 自动生成
        ev_auto = ssp.audit_append(events, {"change_type": "upgraded", "at": T1,
                                            "actor": "operator", "summary": "再次升级（占位）"})
        self.assertTrue(ev_auto["event"].startswith("spe-"))
        # 导出可机读（json.dumps）、保序、且为副本
        exported = ssp.export_audit(events)
        self.assertEqual(exported, events)
        json.dumps(exported, ensure_ascii=False)
        exported[0]["summary"] = "篡改"
        self.assertEqual(events[0]["summary"], "中文技能包升级应用（占位安装会话 ref-0001）")

    # 9. 单槽
    def test_single_slot(self):
        ssp.clear_slot()
        with self.assertRaises(ssp.SkillpackSnapshotError):
            ssp.restore()  # 空槽拒绝还原
        pack_a = sample_pack()
        snap_a = ssp.take_snapshot(pack_a, T0)
        pack_b = sample_pack()
        pack_b["zh-sales-lead-brief/SKILL.md"] = "---\nname: zh-sales-lead-brief\n---\n升级版（占位）\n"
        snap_b = ssp.take_snapshot(pack_b, T1)
        # 新快照顶替旧快照：单槽只留最近一张，restore() 只回上一版
        self.assertNotEqual(snap_b["fingerprint"], snap_a["fingerprint"])
        self.assertEqual(ssp.current_snapshot()["fingerprint"], snap_b["fingerprint"])
        self.assertEqual(ssp.restore(), pack_b)
        self.assertNotEqual(ssp.restore(), pack_a)
        # 还原不顶替单槽：回滚可再回滚
        ssp.restore()
        self.assertEqual(ssp.current_snapshot()["fingerprint"], snap_b["fingerprint"])


if __name__ == "__main__":
    unittest.main()
