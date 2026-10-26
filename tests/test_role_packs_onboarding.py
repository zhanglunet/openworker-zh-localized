# -*- coding: utf-8 -*-
"""PRD-183/T4：开箱指南验收（trend #918）——10 分钟可跟做、步骤可核对。"""
import os
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GUIDE = os.path.join(REPO, "docs", "role-packs-onboarding.md")


class TestOnboardingGuide(unittest.TestCase):
    def test_guide_structure_and_time_budget(self):
        text = open(GUIDE, encoding="utf-8").read()
        self.assertIn("≈10 分钟", text)
        for step in ("1. 取包", "2. 安装", "3. 验证", "4. 迭代/卸载", "5. 发版前"):
            self.assertIn(step, text)

    def test_guide_respects_hard_constraints(self):
        text = open(GUIDE, encoding="utf-8").read()
        self.assertIn("只有一个 `.md`", text)          # install_from_dir 硬约束
        self.assertIn("git URL 安装在本仓不可用", text)  # 动线约束
        self.assertIn("release-gate-role-packs.py", text)  # 发版门

    def test_targets_exist(self):
        self.assertTrue(os.path.isdir(os.path.join(REPO, "role-packs", "hr")))
        self.assertTrue(os.path.isfile(os.path.join(REPO, "role-packs", "terms.txt")))
        self.assertTrue(os.path.isfile(os.path.join(
            REPO, "scripts", "release-gate-role-packs.py")))


if __name__ == "__main__":
    unittest.main()
