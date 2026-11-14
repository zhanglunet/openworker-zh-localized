"""PRD-122/T5：验收——CI 绿 + 抽查 3 节内容对应（trend issue #613）。

抽查节：①一行安装/One-line Install（命令与占位一致）②下载与介绍站/
Downloads（关键链接对齐）③常见问题/FAQ（锚点结构对应）。
运行：uv run --with pytest python -m pytest tests/test_prd122_t5_acceptance.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ZH = (REPO / "README.md").read_text(encoding="utf-8")
EN = (REPO / "README.en.md").read_text(encoding="utf-8")


def _section(text, heading):
    parts = text.split(heading, 1)
    if len(parts) != 2:
        raise AssertionError(f"缺节：{heading}")
    return parts[1].split("\n## ", 1)[0]


def test_sample1_install_section():
    zh = _section(ZH, "## 一行安装")
    en = _section(EN, "## One-line Install")
    assert "bash scripts/install-zh.sh" in zh and \
        "bash scripts/install-zh.sh" in en
    assert "install-zh-demo.svg" in zh and "install-zh-demo.svg" in en
    assert "--check" in zh and "--check" in en


def test_sample2_downloads_section():
    zh = _section(ZH, "## 下载与中文介绍站")
    en = _section(EN, "## Downloads & the Chinese Intro Site")
    # 语义对应（措辞可异）：站点/版本/源码入口
    for key in ("https://oaosf.cn", "v0.1.7-zh"):
        assert key in zh, key
        assert key in en, f"en 缺 {key}"
    assert "website/README.md" in zh and "(website/)" in en


def test_sample3_faq_anchors():
    zh = _section(ZH, "## 7. 常见问题")
    en = _section(EN, "## 7. FAQ")
    # 子锚点数量对应（### 三级标题）
    zh_sub = [ln for ln in zh.splitlines() if ln.startswith("### ")]
    en_sub = [ln for ln in en.splitlines() if ln.startswith("### ")]
    assert len(zh_sub) == len(en_sub), (len(zh_sub), len(en_sub))


def test_ci_checker_and_full_suite_green():
    proc = subprocess.run([sys.executable,
                           str(REPO / "scripts" / "check_readme_sync.py")],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout
    # 本链全部测试子进程复跑（T2/T3/T4 文件）
    for name in ("test_prd122_t2_crosslink.py", "test_prd122_t3_sync_check.py",
                 "test_prd122_t4_sync_en.py"):
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q",
             str(REPO / "tests" / name)],
            capture_output=True, text=True, timeout=300)
        assert proc.returncode == 0, f"{name}: {proc.stdout[-400:]}"
