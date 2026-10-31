# -*- coding: utf-8 -*-
"""PRD-268/T4 自测（trend #1343）：与 PRD-184/211 边界文档——边界齐全。

运行：python3 -m pytest tests/test_prd268_t4_boundary.py -q

覆盖（T1 §3.4 / issue #1343 验收「边界齐全」）：
  文档存在；含 PRD-184 与 PRD-211 专属小节；含「不自动下载图片」声明；
  含对接契约 source_handle / health_meta；含 ASCII 分层图；
  边界一句话在场；占位符纪律（无真实内网 IP/密钥形态字符串）。
虚构纪律：示例一律 example.com 占位；不含真实主机名、账号、密钥。
"""
import re
import unittest
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs" / "plans" / "2026-10-28-prd-268-boundary-184-211.md"


def text() -> str:
    return DOC.read_text(encoding="utf-8")


class TestBoundaryDoc(unittest.TestCase):
    def test_doc_exists(self):
        """边界文档落仓库 docs/plans。"""
        self.assertTrue(DOC.exists(), f"缺少边界文档: {DOC}")

    def test_has_184_and_211_sections(self):
        """含 PRD-184 与 PRD-211 各自的边界小节。"""
        t = text()
        self.assertIn("与 PRD-184", t)
        self.assertIn("与 PRD-211", t)
        # 184 小节：栏目叙事 vs 来源健康 双侧职责都在场
        self.assertIn("栏目内容叙事", t)
        self.assertIn("来源接入健康", t)
        # 184 向 268 要 source_handle；184 不自建请求
        self.assertIn("source_handle", t)
        self.assertIn("不自建请求", t)

    def test_no_auto_download_images_declaration(self):
        """211 边界：素材人工采集审核不变 + 268 不自动下载图片（显式声明）。"""
        t = text()
        self.assertIn("不自动下载图片", t)
        self.assertIn("人工采集", t)

    def test_source_handle_contract(self):
        """对接契约 (source_handle, health_meta) 明文在场。"""
        self.assertIn("health_meta", text())

    def test_ascii_layer_diagram(self):
        """含 ASCII 分层图（围栏代码块，且 268/184/211 三层同图在场）。"""
        t = text()
        blocks = re.findall(r"```[^\n]*\n(.*?)```", t, re.S)
        diagrams = [b for b in blocks if "268" in b and "184" in b and "211" in b]
        self.assertTrue(diagrams, "缺少含三 PRD 分层的 ASCII 图")
        self.assertIn("接入与健康层", diagrams[0])

    def test_boundary_one_liner(self):
        """边界一句话在场：268 管"活着吗"，184/211 管"拿它做什么"。"""
        t = text()
        self.assertIn("268 管", t)
        self.assertIn("中文公开源活着吗", t)
        self.assertIn("拿它做什么", t)

    def test_placeholder_discipline(self):
        """占位符纪律：无真实内网 IP / 密钥形态字符串；示例域名只用 example 系。"""
        t = text()
        for banned in ("192.168.", "10.0.", "172.16.", "127.0.0.1",
                       "password", "secret", "token", "api_key", "apikey"):
            self.assertNotIn(banned, t.lower(), f"疑似敏感串: {banned}")
        self.assertIn("example.com", t)  # 占位符纪律本身在场


if __name__ == "__main__":
    unittest.main()
