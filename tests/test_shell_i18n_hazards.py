"""中文注释/输出与 shell 混排时的两类静默陷阱。

这个仓库的流水线和打包脚本里满是中文，两个坑因此是系统性的、还都不在本机复现：

1. **`$VAR` 紧邻全角字符**。macOS runner 用的是 Apple 自带 bash 3.2，它会把多字节字符
   的首字节吞进变量名，于是 `echo "生成（$RUNNER_OS）"` 在 `set -u` 下报
   `RUNNER_OS<乱码>: unbound variable`。本机 bash 5.2 完全正常 —— 换句话说，
   这个 bug 只在 CI 上出现，而 CI 上的报错信息看起来像是"环境变量没设"。
   （2026-08-06 实测：release-corp.yml 的两个 macOS job 都挂在这里。）
   修法只有一个：写成 `${VAR}`。

2. **Windows runner 的 Python 默认编码是 cp1252**。`open(path)` 读中文 JSON 会
   UnicodeDecodeError，`print(中文)` 往 stdout 写也会 UnicodeEncodeError。
   同一段代码在 Linux/macOS 上完全正常。
   （同一次构建，Windows job 挂在这里。）

两条都不会在本地测试里暴露，所以只能静态扫。
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent

# 扫描范围：会在 CI 上执行的 shell / YAML，以及打包脚本
TARGETS = sorted(
    {
        *ROOT.glob(".github/workflows/*.yml"),
        *ROOT.glob("packaging/*.sh"),
        *ROOT.glob("docs/enterprise/templates/*.yml"),
        *ROOT.glob("docs/enterprise/templates/*.sh"),
    }
)

# $VAR 后面直接跟非 ASCII（且不是 ${VAR} 形式）。排除 $$ 与转义。
_BARE_VAR_THEN_CJK = re.compile(r"(?<![\\$])\$([A-Za-z_][A-Za-z0-9_]*)(?=[^\x00-\x7f])")

# 读文件却没指定编码 —— Windows 上会用 cp1252
_OPEN_NO_ENCODING = re.compile(r"\bopen\(\s*sys\.argv\[[0-9]\]\s*\)")


def _lines(path: Path):
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        yield i, line


def _is_comment(line: str) -> bool:
    """shell / YAML 注释行 —— 注释里的 $VAR 不会被求值。"""
    return line.lstrip().startswith("#")


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: str(p.relative_to(ROOT)))
def test_no_bare_variable_immediately_before_a_wide_character(path):
    """`$VAR）` 必须写成 `${VAR}）`。

    把 release-corp.yml 里的 `${RUNNER_OS}` 改回 `$RUNNER_OS`，这条必须变红。
    """
    hits = [
        (i, m.group(1), line.strip())
        for i, line in _lines(path)
        if not _is_comment(line)
        for m in _BARE_VAR_THEN_CJK.finditer(line)
    ]
    assert not hits, "\n".join(
        f"{path.relative_to(ROOT)}:{i} — ${v} 后面紧跟全角字符，"
        f"macOS 的 bash 3.2 会把它吞进变量名。改成 ${{{v}}}。\n    {line}"
        for i, v, line in hits
    )


@pytest.mark.parametrize("path", TARGETS, ids=lambda p: str(p.relative_to(ROOT)))
def test_embedded_python_reads_files_with_an_explicit_encoding(path):
    """流水线里内嵌的 python 读文件必须显式 encoding —— Windows runner 是 cp1252。"""
    hits = [
        (i, line.strip())
        for i, line in _lines(path)
        if not _is_comment(line) and _OPEN_NO_ENCODING.search(line)
    ]
    assert not hits, "\n".join(
        f"{path.relative_to(ROOT)}:{i} — open() 没指定 encoding，"
        f"Windows runner 上读中文会 UnicodeDecodeError。\n    {line}"
        for i, line in hits
    )


def test_the_scan_actually_covers_the_release_pipeline():
    """扫描范围空了或漏了主流水线，上面两条就成了摆设。"""
    names = {p.name for p in TARGETS}
    assert "release-corp.yml" in names
    assert "build_dmg.sh" in names
    assert len(TARGETS) >= 5


def test_the_pattern_catches_the_real_2026_08_06_failure():
    """用当天真实挂掉的那一行做正样本，防止正则被改松。"""
    bad = 'echo "更新签名产物已生成（$RUNNER_OS）："'
    good = 'echo "更新签名产物已生成（${RUNNER_OS}）："'
    assert _BARE_VAR_THEN_CJK.search(bad)
    assert not _BARE_VAR_THEN_CJK.search(good)


def test_the_pattern_does_not_flag_ascii_neighbours():
    """`$VAR"`、`$VAR/`、`$VAR ` 都是安全的，误报会让人把守卫关掉。"""
    for safe in ('echo "$RUNNER_OS"', 'cd "$HOME"/x', "echo $A $B", 'x="${A}b"'):
        assert not _BARE_VAR_THEN_CJK.search(safe), safe


def test_the_encoding_pattern_distinguishes_fixed_from_broken():
    assert _OPEN_NO_ENCODING.search("json.load(open(sys.argv[1]))")
    assert not _OPEN_NO_ENCODING.search(
        "io.open(sys.argv[1],encoding='utf-8')"
    )
