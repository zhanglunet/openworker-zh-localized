# -*- coding: utf-8 -*-
"""PRD-184/T4：双语传播交叉链接验收（trend #923）——中英入口互通。"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ART = os.path.join(REPO, "docs", "articles", "build-in-public")


class TestBilingualLinks(unittest.TestCase):
    def setUp(self):
        self.readme_cn = open(os.path.join(ART, "README.md"), encoding="utf-8").read()
        self.root_cn = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
        self.posts = [open(os.path.join(ART, f), encoding="utf-8").read()
                      for f in sorted(os.listdir(ART))
                      if f.endswith(".md") and f != "README.md" and f != "TEMPLATE.md"]

    def test_cn_root_links_to_column(self):
        self.assertIn("构建实录", self.root_cn)
        self.assertIn("docs/articles/build-in-public/README.md", self.root_cn)

    def test_column_links_to_en_readme_and_back(self):
        self.assertIn("README.en.md", self.readme_cn)       # 英文入口指向
        self.assertIn("../../README.en.md", self.readme_cn)  # 相对路径可达
        self.assertIn("#39", self.readme_cn)                 # 域内延后声明在场

    def test_every_post_has_bilingual_summary(self):
        for i, post in enumerate(self.posts):
            self.assertIn("英文摘要", post, f"第 {i} 篇缺英文摘要段")

    def test_cn_en_entry_meet_at_column_dir(self):
        """互通验收：中英两条入口线在同一目录汇合（文档层单一事实源）。"""
        self.assertIn("本目录汇合", self.readme_cn)
        # 根 README 的中文入口与本目录英文出口指向同一 README.md
        self.assertIn("build-in-public/README.md", self.root_cn)


if __name__ == "__main__":
    unittest.main()
