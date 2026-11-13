"""PRD-122/T4：中文版改写完成后同步英文（trend issue #612）。

偏差如实声明：T1 的 en 版落后于中文版两次改写（缺「一行安装」与
「开箱加餐 PRD-155」两节，且编号错位 9/10/11）。本单补齐两节+重编号+
两份 TOC 同步；验收钉住两份 H2 结构 1:1 对应。
运行：uv run --with pytest python -m pytest tests/test_prd122_t4_sync_en.py -q
"""
from __future__ import annotations

from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZH = (REPO / "README.md").read_text(encoding="utf-8")
EN = (REPO / "README.en.md").read_text(encoding="utf-8")


def _h2(text):
    return [ln[3:].strip() for ln in text.splitlines()
            if ln.startswith("## ")]


def test_h2_count_matches():
    assert len(_h2(ZH)) == len(_h2(EN)), (len(_h2(ZH)), len(_h2(EN)))


def test_new_sections_present_in_en():
    assert "## One-line Install (Out of the Box)" in EN
    assert "## 9. Bonus: Chinese Context Panel (PRD-155)" in EN
    assert "docs/install-guide-zh.md" in EN
    assert "install-zh-demo.svg" in EN


def test_en_numbering_matches_zh_tail():
    zh_tail = [h for h in _h2(ZH) if h[0].isdigit()][-4:]
    en_tail = [h for h in _h2(EN) if h[0].isdigit()][-4:]
    assert [h.split(".", 1)[0] for h in zh_tail] == \
           [h.split(".", 1)[0] for h in en_tail]


def test_both_tocs_have_install_entry():
    assert "[一行安装（开箱即用）]" in ZH
    assert "[One-line Install (Out of the Box)]" in EN
