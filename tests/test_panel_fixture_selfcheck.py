"""PRD-155/T2：上下文面板演示数据自查断言（T1 §4.3 红线）。

依据：docs/plans/2026-10-23-dsh-context-zh-panel.md（T1）§4.3：
  1. 键名或字符串值命中敏感模式
     ``/(secret|password|credential|api[-_]?key|bearer|private[-_]?key|\\d+\\.\\d+\\.\\d+\\.\\d+)/i``
     即测试失败——沿用 scripts/quality-gate.py 的自查思路，轻量实现（纯标准库）。
  2. 「演示数据」徽标常驻页头，``meta.generator=demo`` 时由代码强制显示，数据文件关不掉。
  3. 时间戳、token 数全虚构；占比五段之和恒为 1.00。
  4. 账号一律 ``<占位符-…>`` 形态（连接器品牌名可出现，令牌/地址/用户名全占位）。

扫描对象：``ui-mocks/fixtures/panel-demo-data.json``（键名 + 字符串值，递归）
与 ``ui-mocks/dsh-context-panel.html``（全文，含页内回退副本与文案常量）。

另附两条一致性守卫：
  - 页内回退副本（file:// 双击打开时 demo 适配器的回退数据源）必须与 fixtures
    文件深度一致，防止两份数据漂移；
  - T1 §3 定稿的 11 条新术语必须在面板文案中逐字出现，防止文案漂移。

可直接 ``python3 tests/test_panel_fixture_selfcheck.py`` 独立运行（无 pytest 环境
也能当门禁脚本用），也随 ``pytest tests -q`` 一起跑。
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIXTURE = ROOT / "ui-mocks" / "fixtures" / "panel-demo-data.json"
PANEL_HTML = ROOT / "ui-mocks" / "dsh-context-panel.html"

# T1 §4.3-3 原文模式：密钥类词 + IPv4 形态
SENSITIVE_RE = re.compile(
    r"(secret|password|credential|api[-_]?key|bearer|private[-_]?key|\d+\.\d+\.\d+\.\d+)",
    re.IGNORECASE,
)

# 契约枚举（T1 §4.1 timeline 字段）
TIMELINE_KINDS = {"user", "assistant", "tool_call", "connector_call", "approval"}
TIMELINE_STATUSES = {"ok", "failed", "retried"}

# T1 §3 标「本稿新增（评审点）」的 11 条新术语（已定稿，面板必须逐字携带）
FINALIZED_NEW_TERMS = [
    "上下文面板",    # panel.title
    "演示数据",      # panel.badge.demo
    "能力组成",      # panel.tab.composition
    "调用演进",      # panel.tab.timeline
    "工具",          # comp.group.tools
    "上下文构成",    # comp.context.title
    "工具定义",      # comp.context.tools
    "技能注入",      # comp.context.skills
    "成功",          # tl.status.ok
    "输入 token",    # tl.tokens.in
    "输出 token",    # tl.tokens.out
]


def _load_fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _walk_strings(node, path="$"):
    """递归产出 JSON 里的 (路径, 键名, 字符串值)；键名与字符串值都要过敏感模式。"""
    if isinstance(node, dict):
        for key, value in node.items():
            yield path, key, None
            yield from _walk_strings(value, f"{path}.{key}")
    elif isinstance(node, list):
        for i, item in enumerate(node):
            yield from _walk_strings(item, f"{path}[{i}]")
    elif isinstance(node, str):
        yield path, None, node


def test_fixture_keys_and_values_are_clean():
    for path, key, value in _walk_strings(_load_fixture()):
        target = key if key is not None else value
        m = SENSITIVE_RE.search(target)
        assert m is None, (
            f"fixtures 命中敏感模式 {m.group(0)!r}（{path} 的 "
            f"{'键名' if key is not None else '字符串值'}）——T1 §4.3-1 红线"
        )


def test_panel_html_text_is_clean():
    html = PANEL_HTML.read_text(encoding="utf-8")
    for i, line in enumerate(html.splitlines(), 1):
        m = SENSITIVE_RE.search(line)
        assert m is None, (
            f"面板 HTML 第 {i} 行命中敏感模式 {m.group(0)!r}——T1 §4.3-1 红线"
        )


def test_context_shares_sum_to_one():
    comp = _load_fixture()["context_composition"]
    assert set(comp) == {"system", "tools", "skills", "connectors", "history"}
    total = sum(seg["share"] for seg in comp.values())
    assert abs(total - 1.0) < 1e-9, f"占比五段之和应为 1.00，实测 {total!r}（T1 §4.3-4）"


def test_connector_accounts_are_placeholders():
    conns = _load_fixture()["capabilities"]["connectors"]
    assert conns, "演示数据应含连接器样例"
    for c in conns:
        assert re.fullmatch(r"<占位符[^>]*>", c["account"]), (
            f"连接器 {c['kind']} 的账号必须为 <占位符-…> 形态，实测 {c['account']!r}（T1 §4.3-1）"
        )


def test_schema_version_and_demo_generator():
    data = _load_fixture()
    assert data["schema_version"] == 1, "schema_version 恒为 1（T1 §4.1）"
    assert data["meta"]["generator"] == "demo", "演示样例 generator 必须为 demo（T1 §4.1）"


def test_timeline_enum_fields_follow_contract():
    for i, ev in enumerate(_load_fixture().get("timeline", [])):
        assert ev["kind"] in TIMELINE_KINDS, f"timeline[{i}].kind={ev['kind']!r} 不在契约枚举内"
        if "status" in ev:
            assert ev["status"] in TIMELINE_STATUSES, (
                f"timeline[{i}].status={ev['status']!r} 不在契约枚举内"
            )


def test_embedded_fallback_matches_fixture():
    """file:// 双击回退副本必须与 fixtures 文件深度一致（防两份演示数据漂移）。"""
    html = PANEL_HTML.read_text(encoding="utf-8")
    m = re.search(
        r'<script type="application/json" id="panel-demo-fallback">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert m, "面板缺少页内回退副本 <script id=panel-demo-fallback>"
    embedded = json.loads(m.group(1))
    assert embedded == _load_fixture(), "页内回退副本与 fixtures/panel-demo-data.json 不一致"


def test_demo_badge_is_forced_by_code_not_data():
    """红线（T1 §4.3-2）：徽标节点默认 hidden，仅渲染层按 meta.generator 打开。"""
    html = PANEL_HTML.read_text(encoding="utf-8")
    assert 'id="demoBadge" hidden' in html, "「演示数据」徽标必须默认隐藏、由代码强制显示"
    assert "generator === 'demo'" in html, "渲染层必须按 meta.generator=demo 强制显示徽标"


def test_finalized_new_terms_present_verbatim():
    """T1 §3 定稿的 11 条新术语必须在面板文案中逐字出现（防文案漂移）。"""
    html = PANEL_HTML.read_text(encoding="utf-8")
    missing = [t for t in FINALIZED_NEW_TERMS if t not in html]
    assert not missing, f"面板缺少已定稿新术语：{missing}"


def _run_standalone() -> int:
    checks = [(name, fn) for name, fn in sorted(globals().items())
              if name.startswith("test_") and callable(fn)]
    failed = 0
    for name, fn in checks:
        try:
            fn()
            print(f"PASS {name}")
        except AssertionError as e:
            failed += 1
            print(f"FAIL {name}: {e}")
    print(f"{len(checks) - failed}/{len(checks)} 项通过")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run_standalone())
