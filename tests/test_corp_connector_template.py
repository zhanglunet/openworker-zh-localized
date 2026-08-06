"""企业内部系统连接器模板（原生描述符 + 内网 HTTP MCP 端点）。

这个模板存在的全部意义，是拿到 stdio 桥拿不到的那两样东西：GUI 卡片，和**逐工具审批**。
所以测试盯的就是这两件事，外加一条：注册不能把上游的注册表搞脏。

注册会改 coworker.connectors 的模块级全局（descriptors.DESCRIPTORS、tool_defs 的四张表）。
测试里每个用例都在 fixture 里完整还原——否则测试之间会互相污染，而且是那种"单跑绿、
全量红"的污染。
"""

from __future__ import annotations

import copy
import importlib.util
import sys
from pathlib import Path

import pytest

TEMPLATE = (
    Path(__file__).resolve().parent.parent
    / "docs" / "enterprise" / "templates" / "connectors" / "corp" / "__init__.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("corp_connector_template", TEMPLATE)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def corp():
    """加载模板并在用例结束后把上游注册表原样还回去。"""
    from coworker.connectors import descriptors as ds
    from coworker.connectors import tool_defs as td

    saved = {
        "DESCRIPTORS": list(ds.DESCRIPTORS),
        "_BY_NAME": dict(ds._BY_NAME),
        "TOOL_DEFS": tuple(td.TOOL_DEFS),
        "TOOL_TO_CONNECTOR": dict(td.TOOL_TO_CONNECTOR),
        "TOOLS_BY_CONNECTOR": copy.deepcopy(
            {k: list(v) for k, v in td.TOOLS_BY_CONNECTOR.items()}
        ),
        "_KIND_BY_NAME": dict(td._KIND_BY_NAME),
        "TARGET_ARGS": dict(td.TARGET_ARGS),
    }
    module = _load()
    try:
        yield module
    finally:
        ds.DESCRIPTORS[:] = saved["DESCRIPTORS"]
        ds._BY_NAME.clear()
        ds._BY_NAME.update(saved["_BY_NAME"])
        td.TOOL_DEFS = saved["TOOL_DEFS"]
        td.TOOL_TO_CONNECTOR.clear()
        td.TOOL_TO_CONNECTOR.update(saved["TOOL_TO_CONNECTOR"])
        td.TOOLS_BY_CONNECTOR.clear()
        td.TOOLS_BY_CONNECTOR.update(saved["TOOLS_BY_CONNECTOR"])
        td._KIND_BY_NAME.clear()
        td._KIND_BY_NAME.update(saved["_KIND_BY_NAME"])
        td.TARGET_ARGS.clear()
        td.TARGET_ARGS.update(saved["TARGET_ARGS"])
        sys.modules.pop("corp_connector_template", None)


# -- 注册 ----------------------------------------------------------------------
def test_register_puts_the_connector_in_the_catalog(corp):
    from coworker.connectors.descriptors import get_descriptor, list_descriptors

    corp.register()
    name = corp.CONFIG["name"]
    assert name in {d.name for d in list_descriptors()}
    d = get_descriptor(name)
    assert d.title and d.blurb and d.instructions, "卡片上三样都要有内容"


def test_register_is_idempotent(corp):
    """挂载点被 import 两次（重载、测试、打包）不该出现两张卡片。"""
    from coworker.connectors import tool_defs as td
    from coworker.connectors.descriptors import DESCRIPTORS

    corp.register()
    corp.register()
    name = corp.CONFIG["name"]
    assert [d.name for d in DESCRIPTORS].count(name) == 1
    tools = [t.name for t in td.TOOL_DEFS]
    assert len(tools) == len(set(tools)), "工具名出现重复"


def test_register_does_not_break_the_upstream_duplicate_guard(corp):
    """上游 test_registry_has_no_duplicate_names 的同一条不变量。"""
    from coworker.connectors import tool_defs as td
    from coworker.connectors.descriptors import DESCRIPTORS

    corp.register()
    names = [d.name for d in DESCRIPTORS]
    assert len(names) == len(set(names))
    tools = [t.name for t in td.TOOL_DEFS]
    assert len(tools) == len(set(tools))


def test_register_keeps_the_four_lookup_tables_in_sync(corp):
    """四张表对不上的那一刻，就是"以为关了其实还开着"。"""
    from coworker.connectors import tool_defs as td

    corp.register()
    for d in corp.build_tool_defs():
        assert td.TOOL_TO_CONNECTOR[d.name] == d.connector
        assert d in td.TOOLS_BY_CONNECTOR[d.connector]
        assert td._KIND_BY_NAME[d.name] == d.kind


# -- 逐工具审批（选这条路的主要理由）-----------------------------------------------
def test_reads_never_gate_and_writes_always_do(corp):
    """这就是模板相对 stdio 桥的核心增量：审批粒度真到工具。

    stdio 桥的 requires_approval 是 server 级的，只能靠读写各起一个 server 近似；
    这里是 prepare_mcp_tools 按 kind 逐个设。

    注意这条测的是**接线**，不是分类对不对——它的期望值就取自 CORP_TOOLS，
    所以把 order_close 标成 read 它不会红（变异验证过）。分类本身由下面的
    test_mutating_tool_names_must_be_declared_write 守着。
    删掉 register() 里 _KIND_BY_NAME 那一行，这条会红。
    """
    from coworker.connectors.tool_defs import approval_for_tool

    corp.register()
    name = corp.CONFIG["name"]
    for tool, _label, kind, _desc in corp.CORP_TOOLS:
        full = f"mcp__{name}__{tool}"
        assert approval_for_tool(full) is (kind != "read"), full


def test_every_declared_tool_has_a_valid_kind(corp):
    for tool, label, kind, desc in corp.CORP_TOOLS:
        assert kind in ("read", "write"), f"{tool} 的 kind 是 {kind!r}"
        assert label and desc, f"{tool} 缺标签或说明"


def test_write_tools_are_actually_declared(corp):
    """模板必须真的示范一个写工具，否则"写要审批"这条路径从没被走过。"""
    assert any(kind == "write" for _t, _l, kind, _d in corp.CORP_TOOLS)


# 会改数据的动词。企业往 CORP_TOOLS 里加工具时，这张表是唯一一道自动防线——
# 把 order_close 标成 read 只会让它静默执行，没人会收到弹框、也没人会发现。
_MUTATING = {
    "create", "update", "delete", "remove", "close", "cancel", "approve",
    "reject", "submit", "set", "add", "post", "put", "patch", "send",
    "write", "upload", "assign", "transfer", "pay", "refund", "import",
}


def test_mutating_tool_names_must_be_declared_write(corp):
    """名字里带改数据动词的工具，kind 必须是 write。

    这条和上面那条不同：它不看 CORP_TOOLS 里写的 kind，而是从工具名独立推断，
    所以把 order_close 标成 read 会被它抓住。
    真有例外（比如接口叫 set_filter 其实只影响查询），在这里显式豁免并写清理由。
    """
    for tool, _label, kind, _desc in corp.CORP_TOOLS:
        verbs = _MUTATING & set(tool.lower().split("_"))
        if verbs:
            assert kind == "write", (
                f"{tool} 名字里有 {sorted(verbs)}，却声明成 {kind}。"
                "会改数据的工具标成 read = 静默执行，没人会收到弹框"
            )


# -- 工具白名单被描述符钉死 --------------------------------------------------------
def test_pinned_allowlist_comes_from_the_template_not_the_endpoint(corp):
    """内网端点哪天多冒出来几个工具也进不来——漂移只能让能力变小。"""
    from coworker.connectors.tool_defs import mcp_pinned_tools

    corp.register()
    pinned = set(mcp_pinned_tools(corp.CONFIG["name"]))
    assert pinned == {t for t, _l, _k, _d in corp.CORP_TOOLS}


def test_tool_names_carry_the_mcp_prefix(corp):
    """前缀对不上，prepare_mcp_tools 就认不回这张表，工具会静默失踪。"""
    name = corp.CONFIG["name"]
    for d in corp.build_tool_defs():
        assert d.name.startswith(f"mcp__{name}__")


def test_no_corp_tool_is_eligible_for_a_standing_rule(corp):
    """常驻授权（§25）只给声明了 target_arg 的工具。内部系统的写操作不该有"以后都别问我"。"""
    from coworker.connectors.tool_defs import target_arg_for

    corp.register()
    for d in corp.build_tool_defs():
        assert target_arg_for(d.name) is None


# -- 凭据校验 -------------------------------------------------------------------
def _resp(status=200, json_body=None, text="", headers=None):
    import httpx

    request = httpx.Request("GET", "https://erp.corp.example.com/api/v2/me")
    if json_body is not None:
        return httpx.Response(status, json=json_body, request=request, headers=headers)
    return httpx.Response(status, text=text, request=request, headers=headers)


@pytest.fixture
def stub_get(monkeypatch):
    import httpx

    box: dict = {}

    def install(response):
        def fake_get(url, **kwargs):
            box["url"] = url
            box["kwargs"] = kwargs
            if isinstance(response, Exception):
                raise response
            return response

        monkeypatch.setattr(httpx, "get", fake_get)
        return box

    return install


def test_validate_reports_the_identity(corp, stub_get):
    box = stub_get(_resp(json_body={"display_name": "张三"}))
    result = corp._validate({"api_base": "https://erp.corp.example.com/api/v2", "api_token": "t"})
    assert result.ok and result.identity == "张三"
    assert box["url"].endswith("/me")


def test_validate_does_not_follow_redirects(corp, stub_get):
    """内网 302 多半是 SSO 登录页：跟过去只会把令牌送给它。"""
    box = stub_get(_resp(302, text="", headers={"location": "https://sso.corp/login"}))
    result = corp._validate({"api_base": "https://erp.corp.example.com/api/v2", "api_token": "t"})
    assert box["kwargs"]["follow_redirects"] is False
    assert result.ok is False and "重定向" in result.error


def test_validate_distinguishes_no_permission_from_outage(corp, stub_get):
    stub_get(_resp(403, json_body={"error": "forbidden"}))
    result = corp._validate({"api_base": "https://x/api", "api_token": "t"})
    assert result.ok is False and "无权" in result.error


def test_validate_reports_network_failure_verbatim(corp, stub_get):
    stub_get(RuntimeError("Name or service not known"))
    result = corp._validate({"api_base": "https://x/api", "api_token": "t"})
    assert result.ok is False and "Name or service not known" in result.error


def test_validate_refuses_without_a_token(corp):
    result = corp._validate({"api_base": "https://x/api"})
    assert result.ok is False and "令牌" in result.error


def test_validate_refuses_without_a_base(corp, monkeypatch):
    monkeypatch.setitem(corp.CONFIG, "api_base", "")
    result = corp._validate({"api_token": "t"})
    assert result.ok is False and "地址" in result.error


def test_validate_never_echoes_the_token(corp, stub_get):
    """凭据不回显——错误信息会进日志、进对话、进截图。"""
    stub_get(_resp(401, json_body={"error": "bad token s3cr3t"}))
    result = corp._validate({"api_base": "https://x/api", "api_token": "s3cr3t"})
    assert "s3cr3t" not in (result.error or "")


def test_validate_rejects_a_body_without_an_identity(corp, stub_get):
    stub_get(_resp(json_body={"unrelated": 1}))
    result = corp._validate({"api_base": "https://x/api", "api_token": "t"})
    assert result.ok is False and "身份" in result.error


# -- 描述符本身 ------------------------------------------------------------------
def test_token_field_is_marked_secret(corp):
    """没标 secret 的字段会在 GUI 里明文显示、并按普通配置回显。"""
    d = corp.build_descriptor()
    token = next(f for f in d.fields if f.key == "api_token")
    assert token.secret is True and token.required is True


def test_descriptor_is_not_two_way_or_a_channel_source(corp):
    """内部系统不是聊天平台。声明成 two_way/channels 会让它出现在"订阅频道"里。"""
    d = corp.build_descriptor()
    assert d.two_way is False and d.channels is False


def test_empty_mcp_url_means_no_one_click(corp, monkeypatch):
    """没有内网 MCP 端点就别选这条路——留空时至少不能假装有一键连接。"""
    monkeypatch.setitem(corp.CONFIG, "mcp_url", "")
    assert corp.build_descriptor().mcp_url == ""


def test_mcp_url_is_env_overridable():
    """测试环境和生产环境要能用同一个包。"""
    import os

    saved = os.environ.get("COWORKER_CORP_MCP_URL")
    os.environ["COWORKER_CORP_MCP_URL"] = "https://mcp.test.corp/mcp"
    try:
        module = _load()
        assert module.CONFIG["mcp_url"] == "https://mcp.test.corp/mcp"
    finally:
        if saved is None:
            os.environ.pop("COWORKER_CORP_MCP_URL", None)
        else:
            os.environ["COWORKER_CORP_MCP_URL"] = saved
        sys.modules.pop("corp_connector_template", None)


# -- 与企业策略的关系 --------------------------------------------------------------
def test_policy_can_deny_the_corp_connector(corp, tmp_path, monkeypatch):
    """连接器白/黑名单对它同样有效——企业自己的连接器也不该是策略之外的特例。"""
    from coworker.catalog_policy import connector_permitted

    corp.register()
    name = corp.CONFIG["name"]

    class _Cfg:
        allowed_connectors = ()
        denied_connectors = (name,)

    assert connector_permitted(name, _Cfg()) is False


def test_policy_allowlist_admits_the_corp_connector(corp):
    from coworker.catalog_policy import connector_permitted

    name = corp.CONFIG["name"]

    class _Cfg:
        allowed_connectors = (name,)
        denied_connectors = ()

    assert connector_permitted(name, _Cfg()) is True
    assert connector_permitted("gmail", _Cfg()) is False
