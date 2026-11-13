"""PRD-121/T4：中文 README 首屏一行安装 + 演示示意图 + 带图安装指南。

trend issue #607。验收：README 首屏有一行安装命令与演示图；指南每步配图、
命令可复制；全部图片文件存在；所有地址只允许占位（example.invalid）。
运行：uv run --with pytest python -m pytest tests/test_prd121_t4_readme_demo.py -q
"""
from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
README = REPO / "README.md"
GUIDE = REPO / "docs" / "install-guide-zh.md"


def test_readme_has_one_line_install():
    text = README.read_text(encoding="utf-8")
    assert "## 一行安装" in text
    assert "bash scripts/install-zh.sh" in text
    # 首屏区（hero 之后、第一个二级大节内）出现演示图
    hero = text.split("## 一行安装", 1)[1]
    assert "install-zh-demo.svg" in hero.split("\n## ", 1)[0]


def test_readme_bilingual_links_intact():
    text = README.read_text(encoding="utf-8")
    assert "./README.md" in text and "./README.en.md" in text


def test_guide_steps_with_images():
    text = GUIDE.read_text(encoding="utf-8")
    for step in range(1, 5):
        assert f"install-zh-step{step}.svg" in text, step
    assert "第 1 步" in text and "第 4 步" in text
    # 命令可复制：bash 代码块存在
    assert text.count("```bash") >= 4


def test_all_referenced_svgs_exist():
    refs = set(re.findall(r"\((assets/[^)]+\.svg|docs/assets/[^)]+\.svg)\)",
                          README.read_text(encoding="utf-8")
                          + GUIDE.read_text(encoding="utf-8")))
    assert refs, "至少引用一张示意图"
    for rel in refs:
        target = REPO / rel if rel.startswith("docs/") else REPO / "docs" / rel
        assert target.exists(), rel


def test_svgs_placeholder_only():
    for svg in (REPO / "docs" / "assets").glob("install-zh-*.svg"):
        text = svg.read_text(encoding="utf-8")
        urls = [w for w in re.findall(r"https?://[^\s<\">&]+", text)]
        allowed = ("example.invalid", "localhost", "www.w3.org")
        bad = [u for u in urls if not any(a in u for a in allowed)]
        assert not bad, (svg.name, bad)
        assert "示意图" in text, svg.name  # 诚实标注非真实截图


def test_no_secrets_in_docs():
    for f in (README, GUIDE):
        text = f.read_text(encoding="utf-8").lower()
        for needle in ("sk-" + "live", "passw" + "ord =",
                       "ghp_" + "x", "akia" + "x"):
            assert needle not in text, f.name
