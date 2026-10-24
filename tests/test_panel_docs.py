# -*- coding: utf-8 -*-
"""PRD-155/T4：开箱文档自查（trend #778）——README 小节 + 指南 + 截图占位。"""
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

    def test_guide_has_steps_and_screenshot_placeholders(self):
        guide = open(os.path.join(REPO, "docs", "context-panel-guide.md"),
                     encoding="utf-8").read()
        steps = re.findall(r"^\d+\. \*\*", guide, re.MULTILINE)
        self.assertGreaterEqual(len(steps), 5, "开箱步骤不足 5 步")
        self.assertGreaterEqual(guide.count("（截图占位"), 2, "截图占位不足 2 处")
        self.assertIn("panel-data v1", guide)

    def test_placeholder_images_declared_not_faked(self):
        guide = open(os.path.join(REPO, "docs", "context-panel-guide.md"),
                     encoding="utf-8").read()
        for name in ("context-panel-composition.png", "context-panel-timeline.png"):
            self.assertIn(name, guide)
            # 占位声明在场；真实截图未入库前不伪造文件
            path = os.path.join(REPO, "docs", "assets", name)
            self.assertFalse(os.path.exists(path), "占位图不应提前伪造")


if __name__ == "__main__":
    unittest.main()
