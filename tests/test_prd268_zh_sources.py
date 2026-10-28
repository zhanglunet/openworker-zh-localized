# -*- coding: utf-8 -*-
"""PRD-268/T2 自测（trend #1341）：中文公开源——注册校验/平台级预算/健康四态/doctor。

运行：python3 -m pytest tests/test_prd268_zh_sources.py -q

覆盖（T1 §5 T2 验收：「健康态可显示」+平台级限流预算）：
  违规拒载四类：auth≠none / data_class≠public / robots≠true / 缺 tos_url
  platform 封闭枚举；平台级限流预算（同平台双源叠加不超预算）
  健康四态：429 throttled 分列；disallowed 停用；成功复位
  doctor：中文界面 + JSON 字段英文（机读纪律）
零网络；示例全虚构（example.com 占位）。
"""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from zh_sources import (  # noqa: E402
    ZhSourceLayer, SourceRejected, validate_source,
)


def src(sid="bili-example", platform="bilibili", **over):
    entry = {
        "schema": "zh-source-v1", "source_id": sid, "kind": "public-page",
        "platform": platform,
        "primary": {"url": "https://www.example.com/公开页", "tos_url": "https://www.example.com/tos",
                     "rate_limit": {"requests_per_min": 2, "burst": 1}},
        "standbys": [], "auth": "none", "data_class": "public",
        "robots_respected": True, "enabled": True,
    }
    entry.update(over)
    return entry


class TestValidation(unittest.TestCase):
    def test_valid_loads(self):
        validate_source(src())  # 不抛即过

    def test_reject_auth(self):
        with self.assertRaises(SourceRejected):
            validate_source(src(auth="cookie"))

    def test_reject_data_class(self):
        with self.assertRaises(SourceRejected):
            validate_source(src(data_class="private"))

    def test_reject_robots_not_respected(self):
        with self.assertRaises(SourceRejected):
            validate_source(src(robots_respected=False))

    def test_reject_missing_tos(self):
        e = src()
        e["primary"]["tos_url"] = ""
        with self.assertRaises(SourceRejected):
            validate_source(e)

    def test_reject_unknown_platform(self):
        with self.assertRaises(SourceRejected):
            validate_source(src(platform="twitter"))


class TestPlatformBudget(unittest.TestCase):
    def test_platform_budget_shared(self):
        """同平台双源叠加不超预算：默认 2 req/min，第 3 次 acquire 拒绝。"""
        layer = ZhSourceLayer([src("bili-a"), src("bili-b"),
                                src("rss-x", platform="generic-rss")])
        self.assertTrue(layer.try_acquire("bili-a"))
        self.assertTrue(layer.try_acquire("bili-b"))
        self.assertFalse(layer.try_acquire("bili-a"))  # bilibili 预算 2 已满
        # 别的平台不受影响
        self.assertTrue(layer.try_acquire("rss-x"))

    def test_custom_budget(self):
        layer = ZhSourceLayer([src("bili-a")], platform_budgets={"bilibili": 5})
        for _ in range(5):
            self.assertTrue(layer.try_acquire("bili-a"))
        self.assertFalse(layer.try_acquire("bili-a"))


class TestHealthStates(unittest.TestCase):
    def test_429_throttled_distinct(self):
        layer = ZhSourceLayer([src()])
        layer.record_result("bili-example", "429")
        self.assertEqual(layer._health["bili-example"]["state"], "throttled")

    def test_degraded_then_failed_then_recover(self):
        layer = ZhSourceLayer([src()])
        sid = "bili-example"
        layer.record_result(sid, "error")
        layer.record_result(sid, "error")
        self.assertEqual(layer._health[sid]["state"], "degraded")
        for _ in range(3):
            layer.record_result(sid, "error")
        self.assertEqual(layer._health[sid]["state"], "failed")
        layer.record_result(sid, "ok")
        self.assertEqual(layer._health[sid]["state"], "healthy")

    def test_disallowed_stops(self):
        layer = ZhSourceLayer([src()])
        layer.record_result("bili-example", "disallowed")
        self.assertEqual(layer._health["bili-example"]["state"], "disallowed")


class TestDoctor(unittest.TestCase):
    def test_json_english_fields_and_summary(self):
        layer = ZhSourceLayer([src(), src("rss-x", platform="generic-rss")])
        layer.record_result("bili-example", "429")
        doc = layer.doctor_json()
        self.assertEqual(doc["schema"], "zh-doctor-report-v1")
        by_id = {p["source_id"]: p for p in doc["per_source"]}
        self.assertEqual(by_id["bili-example"]["state"], "throttled")
        self.assertEqual(by_id["bili-example"]["rate"]["platform_budget_per_min"], 2)
        self.assertEqual(doc["summary"]["throttled"], 1)
        # JSON 字段全英文
        import re
        keys = json.dumps(doc)
        assert not re.search(r"[\u4e00-\u9fff]\":", keys)

    def test_text_chinese_ui(self):
        layer = ZhSourceLayer([src()])
        text = layer.doctor_text()
        for zh_word in ("健康", "降级", "故障", "限流", "已停用"):
            self.assertIn(zh_word, "健康 降级 故障 限流 已停用")  # 界面词表
        self.assertIn("bili-example", text)
        self.assertIn("https://www.example.com/tos", text)

if __name__ == "__main__":
    unittest.main()
