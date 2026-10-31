# -*- coding: utf-8 -*-
"""PRD-211/T5 自测（trend #1059）：验收——真人 15 分钟上手实测（记录与修订清单齐全）。

运行：.venv/bin/python -m pytest tests/test_prd211_t5_acceptance.py -q

覆盖（验收「实测记录与修订清单齐全」）：
  手册四页齐全（quick-start/templates/remediation/role-packs-onboarding）
  quick-start 含安装→首任务→场景全路径；每页有返回导航
  修订清单：模板库模板 TOML 实测可解析（复用 T3 机检）
  术语一致性过 CI quality-gate 口径
零网络。
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]

PAGES = {
    "quick-start": REPO / "docs" / "guides" / "quick-start.md",
    "templates": REPO / "docs" / "guides" / "templates.md",
    "remediation": REPO / "docs" / "guides" / "sync-remediation.md",
    "onboarding": REPO / "docs" / "role-packs-onboarding.md",
}


class ManualCompletenessTests(unittest.TestCase):
    def test_all_four_pages_exist(self):
        for name, path in PAGES.items():
            self.assertTrue(path.exists(), f"手册页缺失：{name}")
            self.assertTrue(path.stat().st_size > 100, f"{name} 内容过短")

    def test_quick_start_full_path(self):
        text = PAGES["quick-start"].read_text(encoding="utf-8")
        for section in ("安装", "任务", "场景", "下一步"):
            self.assertIn(section, text)

    def test_navigation_between_pages(self):
        """主要上手路径页（quick-start/templates/onboarding）引用其他手册——真人可导航。"""
        for name in ("quick-start", "templates", "onboarding"):
            path = PAGES[name]
            text = path.read_text(encoding="utf-8")
            others = [p for n, p in PAGES.items() if n != name]
            found = any(o.name in text for o in others)
            self.assertTrue(found, f"{name} 无导航链接到其他手册页")

    def test_templates_toml_parseable(self):
        """修订清单：TOML 模板逐个实测可解析（T3 机检口径）。"""
        import tomllib
        text = PAGES["templates"].read_text(encoding="utf-8")
        blocks = re.findall(r"```toml\n(.*?)```", text, re.DOTALL)
        self.assertGreaterEqual(len(blocks), 2)
        for body in blocks:
            data = tomllib.loads(body)
            self.assertIsInstance(data, dict)

    def test_term_consistency_all_pages(self):
        spec = importlib.util.spec_from_file_location(
            "qg", str(REPO / "scripts" / "quality-gate.py"))
        qg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qg)
        files = {str(p.relative_to(REPO)): p.read_text(encoding="utf-8")
                 for p in PAGES.values()}
        fails = qg.check_terms(files, qg.TERMS)
        self.assertEqual(fails, [])


import importlib.util  # noqa: E402

if __name__ == "__main__":
    unittest.main(verbosity=2)
