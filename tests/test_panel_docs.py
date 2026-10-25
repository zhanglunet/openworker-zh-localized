# -*- coding: utf-8 -*-
"""PRD-155/T4：开箱文档自查（trend #778）——README 小节 + 指南 + 截图。
T5（trend #779）更新：截图由占位声明翻转为真实入库截图，本自查随之从
「占位不伪造」改为「真实截图已入库且被文档引用」。"""
import os
import re
import unittest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class TestPanelDocs(unittest.TestCase):
    def test_readme_section_and_diff_row(self):
        readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
        self.assertIn("## 9. 开箱加餐：中文上下文面板", readme)
        self.assertIn("ui-mocks/dsh-context-panel.html", readme)
        self.assertIn("docs/context-panel-guide.md", readme)
        self.assertIn("中文上下文面板（能力组成/调用演进可视化）", readme)  # §2 差异表

    def test_guide_has_steps_and_real_screenshots(self):
        guide = open(os.path.join(REPO, "docs", "context-panel-guide.md"),
                     encoding="utf-8").read()
        steps = re.findall(r"^\d+\. \*\*", guide, re.MULTILINE)
        self.assertGreaterEqual(len(steps), 5, "开箱步骤不足 5 步")
        self.assertGreaterEqual(guide.count("（真实截图"), 2, "真实截图声明不足 2 处")
        self.assertNotIn("（截图占位", guide, "T5 起占位声明应已替换为真实截图")
        self.assertIn("panel-data v1", guide)

    def test_real_screenshots_present_and_referenced(self):
        """T5：真实截图已入库且被文档引用（占位阶段的「不伪造」红线如期兑现）。"""
        guide = open(os.path.join(REPO, "docs", "context-panel-guide.md"),
                     encoding="utf-8").read()
        readme = open(os.path.join(REPO, "README.md"), encoding="utf-8").read()
        for name, declared_in in (
            ("context-panel-composition.png", guide),
            ("context-panel-timeline.png", guide),
            ("context-panel-zh.png", readme),
        ):
            self.assertIn(name, declared_in, f"{name} 未被对应文档引用")
            path = os.path.join(REPO, "docs", "assets", name)
            self.assertTrue(os.path.exists(path), f"{name} 真实截图缺失")
            self.assertGreater(os.path.getsize(path), 10_000, f"{name} 疑似空文件")


if __name__ == "__main__":
    unittest.main()
