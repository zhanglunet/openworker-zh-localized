"""PRD-121/T1：中文开箱叙事的一行安装脚本。

验收钉在脚本自身：一条命令、装完说明会看见什么、体检、预演不写文件。
分发地址只允许占位符，不写真实主机、地址、账号或令牌。
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "install-zh.sh"

# 与 tests/test_shell_i18n_hazards.py 同一条：`$VAR）` 在 macOS bash 3.2 会把
# 多字节字符吞进变量名。这里单独扫本脚本，因为那份清单不含 scripts/。
_BARE_VAR_THEN_CJK = re.compile(r"(?<![\\$])\$([A-Za-z_][A-Za-z0-9_]*)(?=[^\x00-\x7f])")
_DOTTED_QUAD = re.compile(r"\b\d{1,3}(?:\.\d{1,3}){3}\b")


def _run(args: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["bash", str(SCRIPT), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        **kwargs,
    )


def test_self_test_passes():
    proc = _run(["--self-test"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "self-test: 通过" in proc.stdout


def test_script_parses():
    subprocess.run(["bash", "-n", str(SCRIPT)], check=True)


def test_help_is_the_chinese_out_of_box_narrative():
    proc = _run(["--help"])
    assert proc.returncode == 0, proc.stderr
    text = proc.stdout
    assert "一行装好，打开就是中文界面。" in text
    assert "应当看见中文界面" in text
    assert "https://example.invalid/openworker-zh/install-zh.sh" in text
    assert "dsh-pet（MIT）" in text
    assert "不制作桌面安装包" in text


def test_dry_run_on_this_repo_writes_nothing():
    venv = ROOT / ".venv"
    state = ROOT / ".openworker-state"
    venv_before = venv.exists()
    state_before = state.exists()
    proc = _run(["--dry-run"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "不会创建虚拟环境，不会安装依赖，不会写入令牌。" in proc.stdout
    assert "一行装好，打开就是中文界面。" in proc.stdout
    assert venv.exists() == venv_before
    assert state.exists() == state_before


def test_check_on_this_repo_writes_nothing():
    state = ROOT / ".openworker-state"
    state_before = state.exists()
    proc = _run(["--check"])
    assert proc.returncode == 0, proc.stdout + proc.stderr
    assert "体检通过" in proc.stdout
    assert state.exists() == state_before


def test_placeholders_only_and_no_copied_install_command():
    text = SCRIPT.read_text(encoding="utf-8")
    assert "example.invalid" in text
    assert "https://github.com" not in text
    assert "dsh plugin" not in text
    assert "dsh-pet-standalone" not in text
    assert _DOTTED_QUAD.search(text) is None
    for forbidden in (
        "/Users/",
        "oaosf",
        "gmail.com",
        "sk-",
        "ghp_",
        "AKIA",
        "npmjs.org",
        "pypi.org",
    ):
        assert forbidden not in text, forbidden


def test_no_bare_variable_immediately_before_a_wide_character():
    hits = []
    for lineno, line in enumerate(SCRIPT.read_text(encoding="utf-8").splitlines(), 1):
        if line.lstrip().startswith("#"):
            continue
        for match in _BARE_VAR_THEN_CJK.finditer(line):
            hits.append(f"{lineno}: ${match.group(1)} in {line.strip()}")
    assert hits == []
