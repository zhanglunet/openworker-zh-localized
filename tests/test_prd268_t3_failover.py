# -*- coding: utf-8 -*-
"""PRD-268/T3 自测（trend #1342）：中文公开源——主备切换与审计。

运行：python3 -m pytest tests/test_prd268_t3_failover.py -q

覆盖（T1 §3.2 / issue #1342 验收「切换有测试」）：
  failed 自动切第一个非 failed 备源：审计事件字段齐全（type/at/source_id/from/to/reason/seq）
  无备源（或门槛不满足）不产事件；恢复探测通过切回留痕 zh_source_restore
  disallowed / failed / 未注册 备源均跳过；事件可 JSON 序列化
  切换不清零计数（consecutive_failures / used_per_min 原样保留）
零网络；示例全虚构（example.com 占位）。
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from zh_sources import (  # noqa: E402
    ZhSourceLayer, AUDIT_FAILOVER, AUDIT_RESTORE,
)


def src(sid="bili-primary", platform="bilibili", standbys=None, **over):
    entry = {
        "schema": "zh-source-v1", "source_id": sid, "kind": "public-page",
        "platform": platform,
        "primary": {"url": "https://www.example.com/公开页", "tos_url": "https://www.example.com/tos",
                     "rate_limit": {"requests_per_min": 2, "burst": 1}},
        "standbys": standbys or [], "auth": "none", "data_class": "public",
        "robots_respected": True, "enabled": True,
    }
    entry.update(over)
    return entry


def fail_primary(layer, sid="bili-primary"):
    """连错 5 次把主源打成 failed（T2 状态机阈值）。"""
    for _ in range(5):
        layer.record_result(sid, "error")
    return layer._health[sid]["state"]


class TestFailover(unittest.TestCase):
    def test_failed_switches_to_standby_event_fields(self):
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")])
        self.assertEqual(fail_primary(layer), "failed")
        ev = layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        self.assertIsNotNone(ev)
        # 事件字段齐全
        self.assertEqual(ev["type"], AUDIT_FAILOVER)
        self.assertEqual(ev["at"], "2026-10-28T12:00:00Z")
        self.assertEqual(ev["source_id"], "bili-primary")
        self.assertEqual(ev["from"], "bili-primary")
        self.assertEqual(ev["to"], "bili-backup")
        self.assertTrue(ev["reason"])
        self.assertEqual(ev["seq"], 1)
        # standby_in_use 更新 + doctor 可见
        self.assertEqual(layer.active_source("bili-primary"), "bili-backup")
        self.assertEqual(layer._health["bili-primary"]["standby_in_use"], "bili-backup")
        doc = {p["source_id"]: p for p in layer.doctor_json()["per_source"]}
        self.assertEqual(doc["bili-primary"]["standby_in_use"], "bili-backup")

    def test_no_standby_no_event(self):
        layer = ZhSourceLayer([src()])
        self.assertEqual(fail_primary(layer), "failed")
        self.assertIsNone(layer.failover("bili-primary", "2026-10-28T12:00:00Z"))
        self.assertEqual(layer.export_events(), [])
        self.assertEqual(layer.active_source("bili-primary"), "bili-primary")

    def test_not_failed_no_event(self):
        """主源未 failed（或已处切换态）时 failover no-op 不产事件。"""
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")])
        layer.record_result("bili-primary", "error")  # 仅 1 次：仍 healthy
        self.assertIsNone(layer.failover("bili-primary", "2026-10-28T12:00:00Z"))
        self.assertEqual(layer.export_events(), [])

    def test_disallowed_and_failed_and_unregistered_standby_skipped(self):
        """disallowed 备源不参与切换；failed/未注册备源同样跳过。"""
        layer = ZhSourceLayer([
            src(standbys=["ghost", "sb-disallowed", "sb-failed", "sb-ok"]),
            src("sb-disallowed"), src("sb-failed"), src("sb-ok"),
        ])
        layer.record_result("sb-disallowed", "disallowed")
        for _ in range(5):
            layer.record_result("sb-failed", "error")
        fail_primary(layer)
        ev = layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        self.assertEqual(ev["to"], "sb-ok")  # 跳过未注册/disallowed/failed，落第一个可用
        self.assertEqual(layer.active_source("bili-primary"), "sb-ok")

    def test_restore_switchback_with_audit(self):
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")])
        fail_primary(layer)
        layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        self.assertIsNone(layer.restore("bili-primary", "2026-10-28T12:01:00Z"))  # 未恢复不切回
        layer.record_result("bili-primary", "ok")  # 恢复探测通过
        ev = layer.restore("bili-primary", "2026-10-28T12:02:00Z")
        self.assertIsNotNone(ev)
        self.assertEqual(ev["type"], AUDIT_RESTORE)
        self.assertEqual(ev["from"], "bili-backup")
        self.assertEqual(ev["to"], "bili-primary")
        self.assertEqual(ev["at"], "2026-10-28T12:02:00Z")
        self.assertEqual(ev["seq"], 2)
        self.assertEqual(layer.active_source("bili-primary"), "bili-primary")
        self.assertEqual([e["type"] for e in layer.export_events()],
                         [AUDIT_FAILOVER, AUDIT_RESTORE])  # 切换与切回全留痕

    def test_failover_preserves_counters(self):
        """切换不清零计数：主源 consecutive_failures / used_per_min 原样保留。"""
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")],
                              platform_budgets={"bilibili": 5})
        self.assertTrue(layer.try_acquire("bili-primary"))  # used_per_min = 1
        fail_primary(layer)
        layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        h = layer._health["bili-primary"]
        self.assertEqual(h["consecutive_failures"], 5)
        self.assertEqual(h["used_per_min"], 1)
        self.assertEqual(h["last_error_class"], "error")
        # 备源计数不受牵连
        self.assertEqual(layer._health["bili-backup"]["consecutive_failures"], 0)

    def test_events_serializable(self):
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")])
        fail_primary(layer)
        layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        layer.record_result("bili-primary", "ok")
        layer.restore("bili-primary", "2026-10-28T12:02:00Z")
        blob = json.dumps(layer.export_events(), ensure_ascii=False)
        parsed = json.loads(blob)
        self.assertEqual(parsed, layer.export_events())
        # 字段名全英文（机读纪律）
        import re
        assert not re.search(r"[\u4e00-\u9fff]\":", blob)


if __name__ == "__main__":
    unittest.main()
