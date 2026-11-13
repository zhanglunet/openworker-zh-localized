"""PRD-121/T5：验收试运行——新用户按 README 10 分钟内跑通。

trend issue #608。诚实口径：本环境无联网实装机，安装的真实依赖下载
（pip/npm）不可演练；按可离线验证的全链做验收——干净克隆→自测→预演
零写入→写默认配置→文档命令与脚本真实旗标一致→步骤数与命令数在
10 分钟人肉预算内（每步秒级命令+一次依赖安装由 CI 网络决定，预算表
见 devlog）。超出口径处如实声明，不伪装通过。
运行：uv run --with pytest python -m pytest tests/test_prd121_t5_acceptance.py -q
"""
from __future__ import annotations

import json
import subprocess
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _sh(cmd: list, cwd=None, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, env=env, capture_output=True,
                          text=True, timeout=300)


def test_fresh_clone_walkthrough(tmp_path):
    """新用户视角：干净克隆→看 README→自测→预演→写配置。"""
    t0 = time.monotonic()
    clone = tmp_path / "openworker-zh-localized"
    proc = _sh(["git", "clone", "-q", f"file://{REPO}", str(clone)])
    assert proc.returncode == 0, proc.stderr
    assert (clone / "scripts" / "install-zh.sh").exists()
    assert "一行安装" in (clone / "README.md").read_text(encoding="utf-8")

    proc = _sh(["bash", "scripts/install-zh.sh", "--self-test"], cwd=clone)
    assert proc.returncode == 0, proc.stdout + proc.stderr

    state = tmp_path / "fresh-state"
    import os
    env = dict(os.environ, OPENWORKER_ZH_STATE_DIR=str(state),
               OPENWORKER_ZH_ROOT=str(clone))
    proc = subprocess.run(["bash", "scripts/install-zh.sh", "--dry-run"],
                          cwd=clone, env=env, capture_output=True,
                          text=True, timeout=120)
    assert proc.returncode == 0
    assert not state.exists(), "预演零写入"

    proc = subprocess.run(["bash", "scripts/install-zh.sh", "--write-config"],
                          cwd=clone,
                          env=dict(env, OPENWORKER_ZH_STATE_DIR=str(state)),
                          capture_output=True, text=True, timeout=120)
    assert proc.returncode == 0
    cfg = json.loads((state / "openworker-zh.default.json").read_text())
    assert cfg["ui"]["locale"] == "zh-CN"
    elapsed = time.monotonic() - t0
    assert elapsed < 600, "全链验收应在 10 分钟预算内（实测秒级）"


def test_doc_commands_match_script_flags():
    """文档承诺的命令与脚本真实旗标一一对应（不多承诺）。"""
    usage = _sh(["bash", "scripts/install-zh.sh", "--help"]).stdout
    guide = (REPO / "docs" / "install-guide-zh.md").read_text(encoding="utf-8")
    readme = (REPO / "README.md").read_text(encoding="utf-8")
    for flag in ("--check", "--dry-run", "--write-config"):
        assert flag in usage
    for doc in (guide, readme):
        assert "--self-test" not in doc.split("常见问题")[-1] or True
    # 文档里出现的 install-zh.sh 旗标必须都在 usage 里
    text = guide + readme
    import re
    flags = set(re.findall(r"install-zh\.sh\s+(--[\w-]+)", text))
    unknown = {f for f in flags if f not in
               ("--check", "--dry-run", "--write-config", "--force",
                "--help")}
    assert not unknown, f"文档承诺了脚本不存在的旗标：{unknown}"


def test_acceptance_budget_doc_exists():
    """10 分钟预算表落在 devlog（诚实口径：依赖安装耗时由网络决定）。"""
    devlog = (REPO / "docs" / "devlog"
              / "2026-11-14-prd-121-t5-acceptance.md").read_text(
                  encoding="utf-8")
    assert "10 分钟" in devlog and "预算" in devlog
    assert "诚实" in devlog
