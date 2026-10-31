# -*- coding: utf-8 -*-
"""PRD-268/T5 验收试运行（trend #1344）：模拟故障切换。

运行：python3 -m pytest tests/test_prd268_acceptance.py -q

验收标准（issue #1344 / T1 §6）：
  1. 注入故障场景 doctor 四态正确（中文界面 + 英文 JSON 字段）
  2. failed 自动切备 + zh_source_failover 审计；恢复切回留痕
  3. 加载器拒绝 auth≠none / 缺 tos_url / robots_respected≠true 条目
  4. 平台级限流预算生效（同平台双源叠加不超预算）
  5. 全程零密钥、无登录墙绕过（代码路径断言 + 扫描）

零网络（只消费调用方喂入的结果码）；示例全虚构（example.com 占位）。
"""
import ast
import json
import re
import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
from zh_sources import (  # noqa: E402
    ZhSourceLayer, SourceRejected, load_registry,
    AUDIT_FAILOVER, AUDIT_RESTORE, FAILOVER_EXCLUDE,
)

DEVLOG = REPO / "docs" / "devlog" / "2026-10-28-prd-268-t5-acceptance.md"


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


def degrade_then_fail(layer, sid="bili-primary"):
    """注入故障时间线：连错使 healthy→degraded(2)→failed(5)，逐步断言。"""
    states = [layer.record_result(sid, "error") for _ in range(5)]
    return states


class TestInjectedFailureTimeline(unittest.TestCase):
    """验收 1+2：注入故障→degraded→failed→failover 切备（事件断言）。"""

    def test_degraded_then_failed_then_failover_with_event(self):
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")])
        states = degrade_then_fail(layer)
        # 故障时间线：1 错 healthy → 2 错 degraded → 5 错 failed
        self.assertEqual(states[0], "healthy")
        self.assertEqual(states[1], "degraded")
        self.assertEqual(states[4], "failed")
        # failed 自动切第一个可用备源；审计事件字段齐全
        ev = layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        self.assertIsNotNone(ev)
        self.assertEqual(ev["type"], AUDIT_FAILOVER)
        self.assertEqual(ev["source_id"], "bili-primary")
        self.assertEqual(ev["from"], "bili-primary")
        self.assertEqual(ev["to"], "bili-backup")
        self.assertEqual(ev["seq"], 1)
        self.assertEqual(layer.active_source("bili-primary"), "bili-backup")
        # 切换不清零计数（供复盘与限流连续性）
        self.assertEqual(layer._health["bili-primary"]["consecutive_failures"], 5)
        # 事件可 JSON 序列化（可机读审计）
        self.assertIn(AUDIT_FAILOVER, json.dumps(layer.export_events(), ensure_ascii=False))

    def test_429_throttled_listed_separately(self):
        layer = ZhSourceLayer([src(), src("bili-b")])
        layer.record_result("bili-primary", "429")
        layer.record_result("bili-b", "error")
        layer.record_result("bili-b", "error")
        report = layer.doctor_json()
        by_id = {p["source_id"]: p for p in report["per_source"]}
        self.assertTrue(by_id["bili-primary"]["throttled"])
        self.assertEqual(by_id["bili-primary"]["state"], "throttled")
        self.assertEqual(by_id["bili-b"]["state"], "degraded")
        # 分列：summary 里 throttled 与 degraded 各自计数
        self.assertEqual(report["summary"]["throttled"], 1)
        self.assertEqual(report["summary"]["degraded"], 1)

    def test_disallowed_standby_excluded_from_failover(self):
        # 备源被平台停用（disallowed）→ 不参与切换；次序取第一个合规备源
        layer = ZhSourceLayer([src(standbys=["bili-banned", "bili-backup"]),
                               src("bili-banned"), src("bili-backup")])
        layer.record_result("bili-banned", "disallowed")
        self.assertEqual(layer._health["bili-banned"]["state"], "disallowed")
        for _ in range(5):
            layer.record_result("bili-primary", "error")
        ev = layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        self.assertEqual(ev["to"], "bili-backup")
        # 全部备源停用 → no-op 不产事件（disallowed 不对抗登录墙/平台处置）
        layer2 = ZhSourceLayer([src(standbys=["only"]), src("only")])
        layer2.record_result("only", "disallowed")
        for _ in range(5):
            layer2.record_result("bili-primary", "error")
        self.assertIsNone(layer2.failover("bili-primary", "2026-10-28T12:00:00Z"))
        self.assertEqual(layer2.export_events(), [])

    def test_recovery_switches_back_with_restore_event(self):
        layer = ZhSourceLayer([src(standbys=["bili-backup"]), src("bili-backup")])
        for _ in range(5):
            layer.record_result("bili-primary", "error")
        layer.failover("bili-primary", "2026-10-28T12:00:00Z")
        # 主源未恢复时 restore no-op
        self.assertIsNone(layer.restore("bili-primary", "2026-10-28T12:05:00Z"))
        # 恢复探测通过（ok）→ 切回留痕 zh_source_restore
        self.assertEqual(layer.record_result("bili-primary", "ok"), "healthy")
        ev = layer.restore("bili-primary", "2026-10-28T12:10:00Z")
        self.assertIsNotNone(ev)
        self.assertEqual(ev["type"], AUDIT_RESTORE)
        self.assertEqual(ev["from"], "bili-backup")
        self.assertEqual(ev["to"], "bili-primary")
        self.assertIsNone(layer._health["bili-primary"]["standby_in_use"])
        self.assertEqual([e["type"] for e in layer.export_events()],
                         [AUDIT_FAILOVER, AUDIT_RESTORE])


class TestLoaderRejectsViolations(unittest.TestCase):
    """验收 3：违规条目拒载——auth≠none / robots≠true / 缺 tos_url。"""

    def test_auth_not_none_rejected_login_wall_not_bypassed(self):
        for bad_auth in ("cookie", "basic", "token"):
            with self.assertRaises(SourceRejected) as ctx:
                ZhSourceLayer([src(auth=bad_auth)])
            self.assertIn("none", str(ctx.exception))

    def test_robots_not_true_rejected(self):
        with self.assertRaises(SourceRejected) as ctx:
            ZhSourceLayer([src(robots_respected=False)])
        self.assertIn("robots", str(ctx.exception))

    def test_missing_tos_rejected_and_registry_partial_load(self):
        with self.assertRaises(SourceRejected) as ctx:
            ZhSourceLayer([src(**{"primary": {"url": "https://www.example.com/x"}})])
        # 混合注册表：违规条目拒载、合规条目照常入层
        import tempfile
        reg = Path(tempfile.mkdtemp(prefix="prd268t5-")) / "registry.json"
        reg.write_text(json.dumps({"sources": [
            src(), src("bad-auth", auth="cookie"), src("bad-robots", robots_respected=False)]},
            ensure_ascii=False), encoding="utf-8")
        ok, rejected = load_registry(reg)
        self.assertEqual([e["source_id"] for e in ok], ["bili-primary"])
        self.assertEqual(len(rejected), 2)
        self.assertEqual([r.source_id for r in rejected], ["bad-auth", "bad-robots"])


class TestPlatformBudget(unittest.TestCase):
    """验收 4：平台级限流预算——同平台双源叠加不超预算。"""

    def test_same_platform_combined_usage_capped(self):
        layer = ZhSourceLayer([src("bili-a"), src("bili-b")])  # 默认预算 2 req/min
        self.assertEqual(layer.platform_budget("bilibili"), 2)
        self.assertTrue(layer.try_acquire("bili-a"))
        self.assertTrue(layer.try_acquire("bili-b"))     # 叠加已到 2
        self.assertFalse(layer.try_acquire("bili-a"))    # 同平台再取被拒（叠加不超）
        # 跨平台互不影响
        layer2 = ZhSourceLayer([src("bili-a"), src("rss-x", platform="generic-rss")])
        self.assertTrue(layer2.try_acquire("bili-a"))
        self.assertTrue(layer2.try_acquire("rss-x"))
        # 预算可显式配置
        layer3 = ZhSourceLayer([src("bili-a"), src("bili-b")], platform_budgets={"bilibili": 3})
        self.assertTrue(all(layer3.try_acquire(s) for s in ("bili-a", "bili-b", "bili-a")))
        self.assertFalse(layer3.try_acquire("bili-b"))


class TestDoctorBilingual(unittest.TestCase):
    """验收 1：doctor 四态正确（中文界面 + 英文 JSON 字段）。"""

    def test_doctor_json_english_fields_and_states(self):
        layer = ZhSourceLayer([src("bili-ok"), src("bili-throttled"), src("bili-failed"),
                               src("bili-banned")])
        layer.record_result("bili-throttled", "429")
        for _ in range(5):
            layer.record_result("bili-failed", "error")
        layer.record_result("bili-banned", "disallowed")
        report = layer.doctor_json()
        self.assertEqual(report["schema"], "zh-doctor-report-v1")
        self.assertEqual(report["summary"],
                         {"total": 4, "healthy": 1, "degraded": 0, "failed": 1,
                          "throttled": 1, "disallowed": 1})
        for row in report["per_source"]:
            for key in ("source_id", "platform", "state", "throttled", "rate",
                        "last_error_class", "tos_url", "standby_in_use"):
                self.assertIn(key, row)  # 字段名英文（机读纪律）

    def test_doctor_text_chinese_readable(self):
        layer = ZhSourceLayer([src("bili-ok"), src("bili-failed")])
        for _ in range(5):
            layer.record_result("bili-failed", "error")
        text = layer.doctor_text()
        self.assertIn("健康", text)
        self.assertIn("故障", text)
        self.assertIn("来源ID", text)
        self.assertIn("bili-ok", text)


class TestNoBypassNoSecrets(unittest.TestCase):
    """验收 5：零密钥、无登录墙绕过（代码路径断言 + 扫描）。"""

    def test_module_imports_no_network_no_login_wall_bypass(self):
        allowed = {"json", "pathlib", "typing", "__future__"}
        banned = {"socket", "urllib", "http", "requests", "httpx", "ssl", "subprocess",
                  "selenium", "playwright", "cookiejar", "base64"}
        src_path = REPO / "scripts" / "zh_sources.py"
        text = src_path.read_text(encoding="utf-8")
        imported = set()
        for node in ast.walk(ast.parse(text)):
            if isinstance(node, ast.Import):
                imported.update(a.name.split(".")[0] for a in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])
        self.assertFalse(imported & banned, f"检出网络/登录绕过面模块: {imported & banned}")
        self.assertTrue(imported <= allowed, f"白名单外依赖: {imported - allowed}")
        # 登录墙语义：源强制 auth=none + robots_respected=true（常量在场，无 cookie/login 代码路径）
        self.assertIn('"auth 必须为 none（不绕登录墙）"', text)
        for banned_word in ("cookie", "login", "password", "session_token"):
            self.assertNotIn(banned_word, text.lower())

    def test_no_secrets_in_module_tests_devlog(self):
        secret_re = re.compile(
            r"sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16}|Bearer\s+[A-Za-z0-9._-]{16,}"
            r"|gh[pousr]_[A-Za-z0-9]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY-----")
        lan_re = re.compile(r"\b(?:10\.\d{1,3}|192\.168|172\.(?:1[6-9]|2\d|3[01]))\.\d{1,3}\.\d{1,3}\b")
        targets = [REPO / "scripts" / "zh_sources.py", Path(__file__), DEVLOG]
        for path in targets:
            text = path.read_text(encoding="utf-8")
            self.assertIsNone(secret_re.search(text), f"{path.name} 检出密钥形态")
            self.assertIsNone(lan_re.search(text), f"{path.name} 检出内网主机名形态")
        # 示例全占位：切换门槛常量在场（disallowed/failed 备源不参与）
        self.assertEqual(set(FAILOVER_EXCLUDE), {"failed", "disallowed"})


if __name__ == "__main__":
    unittest.main()
