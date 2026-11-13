"""PRD-122/T2：中英 README 互链（trend issue #610）。

10-21 批遗留补齐。T1（docs/prd-122-t1-readme-en，已合并）已在两份顶部
放好互链；本单把验收钉住：双向链接存在且指向真实文件。偏差如实声明：
互链在 T1 已交付，本单为钉值测试，无新增文档改动。
运行：uv run --with pytest python -m pytest tests/test_prd122_t2_crosslink.py -q
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def test_zh_links_to_en():
    text = README_ZH.read_text(encoding="utf-8")
    assert "./README.en.md" in text.split("\n## ", 1)[0]


def test_en_links_to_zh():
    text = README_EN.read_text(encoding="utf-8")
    assert "./README.md" in text.split("\n## ", 1)[0]


def test_both_files_exist():
    assert README_ZH.exists() and README_EN.exists()
    assert "中文" in README_ZH.read_text(encoding="utf-8")[:200]
    assert "English" in README_EN.read_text(encoding="utf-8")[:200]


README_ZH = REPO / "README.md"
README_EN = REPO / "README.en.md"
