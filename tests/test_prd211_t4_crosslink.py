# -*- coding: utf-8 -*-
"""PRD-211/T4 自测（trend #1058）：与 PRD-121 开箱叙事互链（叙事页与手册页互相可达）。

运行：.venv/bin/python -m pytest tests/test_prd211_t4_crosslink.py -q

覆盖（验收「叙事页与手册页互相可达」）：
  手册页（quick-start/templates）引用开箱叙事页（role-packs-onboarding）
  叙事页反向引用手册两页——互相可达（双向断言）
  被引用的路径真实存在（链接不悬空）
  术语一致性预检（CI quality-gate 口径）零失败
零网络。
"""
import re
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
QUICK = REPO / "docs" / "guides" / "quick-start.md"
TEMPLATES = REPO / "docs" / "guides" / "templates.md"
STORY = REPO / "docs" / "role-packs-onboarding.md"

LINK_RE = re.compile(r"`(docs/[^`]+\.md)`")


class CrossLinkTests(unittest.TestCase):
    def test_manual_pages_link_to_story(self):
        for path in (QUICK, TEMPLATES):
            text = path.read_text(encoding="utf-8")
            self.assertIn("role-packs-onboarding.md", text,
                          f"{path.name} 未引用开箱叙事页")

    def test_story_links_back_to_manual_pages(self):
        text = STORY.read_text(encoding="utf-8")
        self.assertIn("guides/quick-start.md", text)
        self.assertIn("guides/templates.md", text)

    def test_links_resolve_to_real_files(self):
        """链接不悬空：被引用的相对路径在仓库内真实存在。"""
        for path in (QUICK, TEMPLATES, STORY):
            text = path.read_text(encoding="utf-8")
            for ref in LINK_RE.findall(text):
                self.assertTrue((REPO / ref).exists(), f"{path.name} 引用悬空：{ref}")

    def test_term_consistency_clean(self):
        """CI quality-gate 术语口径预检零失败。"""
        import importlib.util
        spec = importlib.util.spec_from_file_location("qg", str(REPO / "scripts" / "quality-gate.py"))
        qg = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(qg)
        files = {str(p.relative_to(REPO)): p.read_text(encoding="utf-8")
                 for p in (QUICK, TEMPLATES, STORY)}
        fails = qg.check_terms(files, qg.TERMS)
        self.assertEqual(fails, [])


if __name__ == "__main__":
    unittest.main()
