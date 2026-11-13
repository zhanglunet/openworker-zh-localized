"""PRD-122/T3：章节同步检查（trend issue #611）。

验收：CI 比对标题结构，不一致时报错。检查器 exit 0=同步；人为破坏
drift 时必须 exit 1（以函数级注入模拟，不真改仓库文件）。
运行：uv run --with pytest python -m pytest tests/test_prd122_t3_sync_check.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "check_readme_sync.py"

sys.path.insert(0, str(SCRIPT.parent))
import check_readme_sync as crs  # noqa: E402


def test_checker_passes_now():
    assert crs.check() == []


def test_checker_detects_drift(monkeypatch):
    original = crs.h2_list
    en = (REPO / "README.en.md").read_text(encoding="utf-8")
    drifted = en.replace("## 7. FAQ", "## 7. Frequently Asked Questions")
    monkeypatch.setattr(
        crs, "h2_list",
        lambda text: original(drifted if text.strip().startswith(
            "# OpenWorker") else text))
    problems = crs.check()
    assert problems and any("en 标题" in p for p in problems)


def test_self_test_exit_zero():
    proc = subprocess.run([sys.executable, str(SCRIPT)],
                          capture_output=True, text=True, timeout=60)
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_workflow_has_sync_step():
    yml = (REPO / ".github" / "workflows" / "i18n-check.yml").read_text(
        encoding="utf-8")
    assert "check_readme_sync.py" in yml
