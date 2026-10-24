"""PRD-155/T5：上下文面板开箱验收测试（按 docs/context-panel-guide.md 逐步走查）。

依据：docs/context-panel-guide.md「开箱步骤（10 分钟内）」①~⑤ 与 PRD-155 T5 验收标准
（trend #779）：中文用户按文档 10 分钟内看懂面板；无密钥。

形态说明：仓库无浏览器自动化（playwright/selenium）惯例，既有测试惯例是
``http.server`` 起本机回环静态服务（参照 tests/test_kb_server.py），故本验收采用
**HTTP + 页面字符串检查**：把 ``ui-mocks/`` 起在回环临时端口上，按指南步骤逐条断言。
人工浏览器走查（逐步计时、双页签与节点详情可点开）记录在
``docs/context-panel-acceptance.md``（T5 验收记录），与本自动化互为印证。

覆盖（指南步骤 → 断言）：
  ① 打开面板（双击/HTTP 等价）：HTML 可服务、双页签在场、file:// 页内回退副本
     与 fixtures 契约文件深度一致（双击形态与 HTTP 形态数据同源）；
  ② 切换主题：data-theme 明暗双主题样式与切换逻辑在场；
  ③ 看组成：五段占比 + 合计 token 口径、装配清单六行标签、账号占位符；
  ④ 看演进：页签②启用、节点列/详情容器、默认选中首节点、详情三指标
     （输入/输出 token、耗时）与状态三态（✓/✕/↻）；
  ⑤ 换数据：panel-data v1 契约闸（schema_version ≠ 1 拒绝渲染）、demo 适配器
     fetch→页内回退双通道、coworker 适配器留桩不猜端点。

另含 T5 密钥扫描（面板数据 + 面板文档）：演示数据 JSON、面板 HTML、
``docs/context-panel-guide.md``、``docs/context-panel-acceptance.md``、
README §9（开箱加餐小节）均不得命中 T1 §4.3-1 敏感模式。

可直接 ``python3 tests/test_panel_acceptance_t5.py`` 独立运行（纯标准库），
也随 ``pytest tests -q`` 一起跑。
"""
from __future__ import annotations

import json
import re
import sys
import threading
import urllib.request
from functools import partial
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_MOCKS = ROOT / "ui-mocks"
GUIDE = ROOT / "docs" / "context-panel-guide.md"
ACCEPTANCE = ROOT / "docs" / "context-panel-acceptance.md"
README = ROOT / "README.md"
FIXTURE = UI_MOCKS / "fixtures" / "panel-demo-data.json"
PANEL_HTML = UI_MOCKS / "dsh-context-panel.html"

# 与 tests/test_panel_fixture_selfcheck.py 同一敏感模式（T1 §4.3-1）：
# 密钥类词 + IPv4 形态（文档与数据一律占位符，不写真实地址）
SENSITIVE_RE = re.compile(
    r"(secret|password|credential|api[-_]?key|bearer|private[-_]?key|\d+\.\d+\.\d+\.\d+)",
    re.IGNORECASE,
)

# 指南步骤④勘误后的真实交互（T5 验收记录有说明）：无 ◀ ▶/自动回放，
# 交互形态 = 点击节点 + 键盘方向键切换页签
NODE_METRIC_LABELS = ("输入 token", "输出 token", "耗时")
STATUS_GLYPHS = ("✓", "✕", "↻")
TAB_LABELS = ("① 能力组成", "② 调用演进")


class _PanelSite:
    """把 ui-mocks/ 起在本机回环临时端口（仅测试进程内，用完即关）。"""

    def __init__(self) -> None:
        handler = partial(SimpleHTTPRequestHandler, directory=str(UI_MOCKS))
        self._server = HTTPServer(("127.0.0.1", 0), handler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()
        self.base = f"http://127.0.0.1:{self._server.server_port}"

    def get(self, path: str) -> tuple[int, str, str]:
        with urllib.request.urlopen(f"{self.base}/{path}", timeout=5) as res:
            body = res.read().decode("utf-8")
            return res.status, res.headers.get("Content-Type", ""), body

    def close(self) -> None:
        self._server.shutdown()
        self._server.server_close()
        self._thread.join(timeout=5)


_SITE: _PanelSite | None = None


def _site() -> _PanelSite:
    global _SITE
    if _SITE is None:
        _SITE = _PanelSite()
    return _SITE


def _fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def _panel_html() -> str:
    return PANEL_HTML.read_text(encoding="utf-8")


def _readme_panel_section() -> str:
    """README「## 9. 开箱加餐」小节（面板相关内容，下一个二级标题前）。"""
    text = README.read_text(encoding="utf-8")
    m = re.search(r"(## 9\. 开箱加餐.*?)(?=\n## )", text, re.DOTALL)
    assert m, "README 缺少 §9 开箱加餐小节"
    return m.group(1)


def teardown_module() -> None:
    if _SITE is not None:
        _SITE.close()


# ---------------------------------------------------------------- 指南步骤①
def test_step1_open_panel_serves_html_with_both_tabs():
    """① 打开面板：HTTP 形态可打开（与双击 file:// 等价），双页签默认落在①。"""
    status, ctype, body = _site().get("dsh-context-panel.html")
    assert status == 200 and "text/html" in ctype, f"面板 HTML 服务失败：{status} {ctype}"
    assert "<title>OpenWorker 上下文面板</title>" in body
    for label in TAB_LABELS:
        assert label in body, f"缺少页签 {label!r}"
    # 默认落在①：composition 视图不隐藏、timeline 视图默认隐藏
    assert re.search(r'<section id="view-composition"(?![^>]*hidden)', body)
    assert re.search(r'<section id="view-timeline"[^>]*hidden', body)


def test_step1_doubleclick_fallback_equals_fixture():
    """① 双击（file://）形态：页内回退副本与 fixtures 契约文件深度一致。"""
    html = _panel_html()
    m = re.search(
        r'<script type="application/json" id="panel-demo-fallback">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert m, "缺少页内回退副本"
    assert json.loads(m.group(1)) == _fixture(), "双击形态数据与 HTTP 形态数据不同源"


def test_step2_theme_toggle_wired():
    """② 切换主题：明暗双主题样式 + 右上角按钮切换 data-theme 的逻辑在场。"""
    html = _panel_html()
    assert '<html lang="zh-CN" data-theme="light">' in html, "默认应为亮色主题"
    assert 'html[data-theme="dark"]' in html, "缺少暗色主题样式块"
    assert 'id="themeBtn"' in html, "缺少右上角主题按钮"
    assert "dataset.theme === 'dark' ? 'light' : 'dark'" in html, "缺少主题切换逻辑"


def test_step3_composition_segments_and_total():
    """③ 看组成：五段占比条 + 合计 token 口径（「本地聚合」标注文案）。"""
    comp = _fixture()["context_composition"]
    assert set(comp) == {"system", "tools", "skills", "connectors", "history"}
    assert abs(sum(seg["share"] for seg in comp.values()) - 1.0) < 1e-9
    html = _panel_html()
    assert "（token 占比，合计" in html, "缺少合计 token 口径文案"
    for label in ("系统提示", "工具定义", "技能注入", "连接器说明", "历史会话串"):
        assert label in html, f"缺少占比段标签 {label!r}"
    # 装配清单六行标签（comp.group.* 文案键）
    for key, label in (
        ("comp.group.model", "模型"), ("comp.group.persona", "角色"),
        ("comp.group.skills", "技能"), ("comp.group.connectors", "连接器"),
        ("comp.group.tools", "工具"), ("comp.group.approvals", "审批"),
    ):
        assert f"'{key}':" in html, f"缺少装配清单文案键 {key}"
        assert label in html, f"缺少装配清单标签 {label!r}"


def test_step3_connector_accounts_are_placeholders():
    """③ 看组成：连接器账号一律占位符（不出现真实账号）。"""
    for c in _fixture()["capabilities"]["connectors"]:
        assert re.fullmatch(r"<占位符[^>]*>", c["account"]), c["account"]


def test_step4_timeline_tab_enabled_with_node_detail_chain():
    """④ 看演进：页签②可点 → 节点列上屏 → 点击节点出详情卡，全链路元素在场。"""
    html = _panel_html()
    # 页签②启用（无 disabled），点击可切换
    m = re.search(r'<button id="tabTimeline"[^>]*>', html)
    assert m and "disabled" not in m.group(0)
    assert "selectTab(name)" in html or "selectTab(" in html
    # 节点列 + 详情容器 + 事件绑定
    assert 'id="tlRail"' in html and 'id="tlDetail"' in html
    assert "addEventListener('click', () => selectTimelineNode(Number(btn.dataset.i)))" in html
    # 默认选中首节点（详情即时可见）
    assert "selectTimelineNode(0)" in html
    # 详情三指标标签
    for label in NODE_METRIC_LABELS:
        assert label in html, f"缺少详情指标 {label!r}"
    # 状态三态字形（✓ 成功 / ✕ 失败 / ↻ 已重试）
    for glyph, name in zip(STATUS_GLYPHS, ("ok", "failed", "retried")):
        assert f"{name}: '{glyph}'" in html, f"缺少状态字形 {name}"


def test_step4_demo_timeline_demonstrable():
    """④ 看演进：演示数据 5 种节点 + 3 种状态全覆盖（详情卡可演示失败→已重试）。"""
    timeline = _fixture()["timeline"]
    kinds = {ev["kind"] for ev in timeline}
    statuses = {ev["status"] for ev in timeline if "status" in ev}
    assert kinds == {"user", "assistant", "tool_call", "connector_call", "approval"}
    assert statuses == {"ok", "failed", "retried"}
    assert any(ev["kind"] == "tool_call" and ev["status"] == "retried" for ev in timeline), (
        "演示数据应含失败→已重试管线（file_read 两连节点）"
    )


def test_step5_contract_gate_rejects_non_v1():
    """⑤ 换数据：渲染层只认 panel-data v1——schema_version ≠ 1 拒绝渲染。"""
    html = _panel_html()
    assert "PANEL_SCHEMA_VERSION = 1" in html
    assert "schema_version !== PANEL_SCHEMA_VERSION" in html
    assert "数据源版本不支持" in html  # 契约固定文案（T1 §4.1）
    assert _fixture()["schema_version"] == 1


def test_step5_demo_adapter_dual_channel_and_coworker_stub():
    """⑤ 换数据：demo 适配器 fetch→页内回退双通道；coworker 适配器留桩不猜端点。"""
    html = _panel_html()
    assert "fetch('fixtures/panel-demo-data.json')" in html, "HTTP 形态应先取 fixtures 契约文件"
    assert "panel-demo-fallback" in html, "file:// 形态应回退页内副本"
    assert "coworker 适配器尚未实现" in html, "coworker 适配器应留桩（不预设端点形状）"


# ------------------------------------------------------------ T5 密钥扫描
def test_t5_keyscan_panel_fixture_keys_and_values():
    """无密钥：演示数据 JSON 键名与字符串值不得命中敏感模式（T1 §4.3-1）。"""
    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                yield key
                yield from walk(value)
        elif isinstance(node, list):
            for item in node:
                yield from walk(item)
        elif isinstance(node, str):
            yield node

    for target in walk(_fixture()):
        m = SENSITIVE_RE.search(target)
        assert m is None, f"演示数据命中敏感模式 {m.group(0)!r}"


def test_t5_keyscan_panel_html():
    """无密钥：面板 HTML（含页内回退副本与文案常量）逐行扫描。"""
    for i, line in enumerate(_panel_html().splitlines(), 1):
        m = SENSITIVE_RE.search(line)
        assert m is None, f"面板 HTML 第 {i} 行命中敏感模式 {m.group(0)!r}"


def test_t5_keyscan_panel_docs():
    """无密钥：面板相关文档（使用指南 / T5 验收记录 / README §9）逐行扫描。"""
    targets = {"指南": GUIDE, "验收记录": ACCEPTANCE, "README §9": None}
    for name, path in targets.items():
        text = _readme_panel_section() if path is None else path.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            m = SENSITIVE_RE.search(line)
            assert m is None, f"{name} 第 {i} 行命中敏感模式 {m.group(0)!r}"


def _run_standalone() -> int:
    checks = [(n, f) for n, f in sorted(globals().items())
              if n.startswith("test_") and callable(f)]
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
