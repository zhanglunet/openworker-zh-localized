"""PRD-121/T2：默认中文配置（装后默认中文界面，配置只含占位符）。

trend issue #605。T1 设计的配置件未落地，本单补齐：
  - bash scripts/install-zh.sh --write-config 写 ${STATE}/openworker-zh.default.json；
  - 默认 locale=zh-CN；base_url 等全部占位（example.invalid）；密钥只给
    环境变量名不写值；600 权限；重复执行逐字节一致（恢复默认语义）；
  - --dry-run 仍零写入；--self-test（含 T1 可移植性修复 BASH_ABS）全过。
运行：uv run --with pytest python -m pytest tests/test_prd121_t2_default_config.py -q
"""
from __future__ import annotations

import json
import os
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "install-zh.sh"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["bash", str(SCRIPT), *args],
                          capture_output=True, text=True, timeout=120)


def _write_config(tmp: Path) -> Path:
    state = tmp / "state-out"
    env = dict(os.environ, OPENWORKER_ZH_STATE_DIR=str(state))
    proc = subprocess.run(["bash", str(SCRIPT), "--write-config"],
                          capture_output=True, text=True, env=env,
                          timeout=120)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    return state / "openworker-zh.default.json"


def test_write_config_creates_valid_json(tmp_path):
    cfg = _write_config(tmp_path)
    assert cfg.exists()
    data = json.loads(cfg.read_text(encoding="utf-8"))
    assert data["schema"] == "openworker-zh-default-config/v1"
    assert data["ui"]["locale"] == "zh-CN"
    assert data["ui"]["first_run"] == "zh"


def test_config_only_placeholders(tmp_path):
    cfg = _write_config(tmp_path)
    text = cfg.read_text(encoding="utf-8")
    urls = [w for w in text.split('"') if w.startswith("http")]
    assert urls, "应有占位地址"
    assert all(u.startswith("https://example.invalid") for u in urls)


def test_no_secret_values(tmp_path):
    cfg = _write_config(tmp_path)
    text = cfg.read_text(encoding="utf-8")
    assert "OPENWORKER_ZH_API_KEY" in text      # 只给环境变量名
    for needle in ("sk-" + "live", "passw" + "ord", "ghp_" + "x",
                   "AKIA" + "x"):
        assert needle not in text
    assert text.count("OPENWORKER_ZH_API_KEY") == 1


def test_permission_600(tmp_path):
    cfg = _write_config(tmp_path)
    mode = stat.S_IMODE(cfg.stat().st_mode)
    assert mode == 0o600


def test_idempotent_reset(tmp_path):
    first = _write_config(tmp_path).read_bytes()
    second = _write_config(tmp_path).read_bytes()
    assert first == second


def test_dry_run_writes_nothing(tmp_path):
    state = tmp_path / "state-dry"
    env = dict(os.environ, OPENWORKER_ZH_STATE_DIR=str(state))
    proc = subprocess.run(["bash", str(SCRIPT), "--dry-run"],
                          capture_output=True, text=True, env=env,
                          timeout=120)
    assert proc.returncode == 0
    assert not state.exists(), "预演不得写任何文件"


def test_self_test_passes():
    proc = _run("--self-test")
    assert proc.returncode == 0, proc.stdout + proc.stderr


def test_script_syntax_ok():
    proc = subprocess.run(["bash", "-n", str(SCRIPT)],
                          capture_output=True, text=True)
    assert proc.returncode == 0, proc.stderr
