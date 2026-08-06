"""企业内部系统 HTTP API → MCP 桥。

这个桥站在「模型说的话」和「内网系统的写接口」之间，所以测试的重点不是它能不能查到订单，
而是它**不能**做什么：

* 路径参数不能拐去别的接口（转义 + base_url 前缀双保险）
* 不能跟随重定向 —— 一个 302 就能把 Authorization 头送到别的 host
* 响应必须按字段白名单裁剪 —— 内网记录里的身份证号不该整包进模型上下文
* 会改数据的接口必须在配置里显式承认自己会改数据
* 凭据只从环境变量取，写进 spec 就拒绝加载

每条守卫都做过变异测试：把守卫删掉，对应用例必须变红。
"""

from __future__ import annotations

import asyncio
import importlib.util
import json
from pathlib import Path

import httpx
import pytest

SERVER = (
    Path(__file__).resolve().parent.parent
    / "docs" / "enterprise" / "templates" / "mcp" / "corp-api" / "server.py"
)
TEMPLATE_DIR = SERVER.parent


def _load():
    spec = importlib.util.spec_from_file_location("corp_api_server", SERVER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


api = _load()

BASE = "https://erp.corp.example.com/api/v2"


# -- 脚手架 --------------------------------------------------------------------
def _spec(tools, **top):
    out = {"base_url": BASE, "tools": tools}
    out.update(top)
    return out


def _get_tool(**over):
    tool = {
        "name": "corp_order_get",
        "description": "查订单",
        "method": "GET",
        "path": "/orders/{order_no}",
        "params": [
            {"name": "order_no", "type": "string", "in": "path", "required": True}
        ],
    }
    tool.update(over)
    return tool


def _bridge(spec, *, handler=None, monkeypatch=None):
    bridge = api.Bridge(spec)
    if handler is not None:
        bridge._transport = httpx.MockTransport(handler)
    return bridge


def _call(bridge, name, args):
    return asyncio.run(bridge.call(name, args))


def _seen(box):
    """记录请求并回一个固定 JSON，供断言"用什么地址、带什么头发出去了"。"""

    def handler(request: httpx.Request) -> httpx.Response:
        box.append(request)
        return httpx.Response(200, json={"order_no": "SO1", "status": "closed"})

    return handler


@pytest.fixture
def token(monkeypatch):
    monkeypatch.setenv("CORP_API_TOKEN", "s3cr3t-token")
    return "s3cr3t-token"


# -- 守卫 1：路径参数不能拐去别的接口 ---------------------------------------------
def test_path_param_cannot_escape_to_another_endpoint(token):
    """`{order_no}` 传 `../../admin/users` 必须仍然打在 /orders/ 下面。

    把 quote(..., safe="") 改成 safe="/" 这条必须变红——那正是一次换接口的越权调用。
    """
    seen: list[httpx.Request] = []
    bridge = _bridge(
        _spec([_get_tool()], auth={"type": "bearer", "token_env": "CORP_API_TOKEN"}),
        handler=_seen(seen),
    )
    res = _call(bridge, "corp_order_get", {"order_no": "../../admin/users"})
    assert res["ok"] is True
    url = str(seen[0].url)
    assert url.startswith(BASE + "/orders/"), url
    assert "/admin/users" not in url, url
    assert "%2F" in url  # 斜杠被转义成了普通字符，不是路径分隔符


def test_path_param_cannot_inject_a_query_string(token):
    seen: list[httpx.Request] = []
    bridge = _bridge(_spec([_get_tool()]), handler=_seen(seen))
    _call(bridge, "corp_order_get", {"order_no": "SO1?admin=1"})
    url = str(seen[0].url)
    assert url == BASE + "/orders/SO1%3Fadmin%3D1", url


def test_build_url_refuses_to_leave_base_url():
    """纵深防御：即使转义被改坏，越界的地址也要在发出去之前就被拦下。"""
    bridge = api.Bridge(_spec([_get_tool()]))
    endpoint = bridge.tools["corp_order_get"]
    with pytest.raises(ValueError, match="越出 base_url"):
        bridge.build_url(endpoint, "/../../../other-api/admin")


def test_build_url_accepts_a_normal_path():
    bridge = api.Bridge(_spec([_get_tool()]))
    endpoint = bridge.tools["corp_order_get"]
    assert bridge.build_url(endpoint, "/orders/SO1") == BASE + "/orders/SO1"


def test_build_url_keeps_a_trailing_slash():
    """normpath 会吃掉尾斜杠，有些接口靠它区分集合与单条。"""
    bridge = api.Bridge(_spec([_get_tool()]))
    endpoint = bridge.tools["corp_order_get"]
    assert bridge.build_url(endpoint, "/orders/") == BASE + "/orders/"


def test_build_url_normalizes_harmless_dot_segments():
    bridge = api.Bridge(_spec([_get_tool()]))
    endpoint = bridge.tools["corp_order_get"]
    assert bridge.build_url(endpoint, "/orders/./SO1") == BASE + "/orders/SO1"


def test_build_url_refuses_to_climb_to_the_host_root():
    bridge = api.Bridge(_spec([_get_tool()]))
    endpoint = bridge.tools["corp_order_get"]
    with pytest.raises(ValueError):
        bridge.build_url(endpoint, "/../v1/orders")


# -- 守卫 2：不跟随重定向 --------------------------------------------------------
def test_redirect_is_not_followed_and_credentials_do_not_leak(token):
    """302 → 另一个 host。跟过去等于把 Authorization 头发给它。"""
    hosts: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        hosts.append(request.url.host)
        return httpx.Response(302, headers={"location": "https://evil.example.com/collect"})

    bridge = _bridge(
        _spec([_get_tool()], auth={"type": "bearer", "token_env": "CORP_API_TOKEN"}),
        handler=handler,
    )
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert res["ok"] is False
    assert hosts == ["erp.corp.example.com"], "只应打过内网那一次"
    assert "evil.example.com" in res["error"]
    assert token not in json.dumps(res, ensure_ascii=False)


# -- 守卫 3：响应字段白名单 ------------------------------------------------------
def test_fields_whitelist_drops_undeclared_response_fields(token):
    """内网记录会顺手带出身份证号、薪资。没声明的字段不该进模型上下文。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "order_no": "SO1",
                "status": "closed",
                "customer": {"name": "张三", "id_card": "110101199001011234"},
                "internal_margin": 0.42,
            },
        )

    bridge = _bridge(
        _spec([_get_tool(fields=["order_no", "status", "customer.name"])]),
        handler=handler,
    )
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    data = json.loads(res["data"])
    assert data == {"order_no": "SO1", "status": "closed", "customer": {"name": "张三"}}
    assert "id_card" not in res["data"]
    assert "internal_margin" not in res["data"]


def test_fields_whitelist_applies_inside_lists(token):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "total": 2,
                "results": [
                    {"order_no": "SO1", "status": "open", "cost": 1},
                    {"order_no": "SO2", "status": "closed", "cost": 2},
                ],
            },
        )

    tool = _get_tool(
        name="corp_order_search",
        path="/orders",
        params=[],
        fields=["total", "results.order_no", "results.status"],
    )
    bridge = _bridge(_spec([tool]), handler=handler)
    data = json.loads(_call(bridge, "corp_order_search", {})["data"])
    assert data["results"] == [
        {"order_no": "SO1", "status": "open"},
        {"order_no": "SO2", "status": "closed"},
    ]
    assert "cost" not in json.dumps(data)


def test_no_fields_declared_returns_the_whole_body(token):
    """不写 fields 就是不裁剪——白名单是可选的，但选了就要真的收紧。"""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"a": 1, "b": {"c": 2}})

    bridge = _bridge(_spec([_get_tool()]), handler=handler)
    assert json.loads(_call(bridge, "corp_order_get", {"order_no": "x"})["data"]) == {
        "a": 1,
        "b": {"c": 2},
    }


def test_pick_fields_keeps_missing_keys_out_instead_of_raising():
    tree = api._field_tree(["a", "b.c"])
    assert api.pick_fields({"a": 1}, tree) == {"a": 1}
    assert api.pick_fields({"b": {"d": 9}}, tree) == {"b": {}}


# -- 守卫 4：写接口必须显式承认 ---------------------------------------------------
def test_non_safe_method_without_write_flag_fails_to_load():
    """POST 却没写 "write": true → 加载即失败。

    哪些工具会改数据，必须是配置里看得见的事实。删掉这条检查，测试必须变红。
    """
    tool = _get_tool(name="corp_order_close", method="POST", path="/orders/{order_no}/close")
    with pytest.raises(api.SpecError, match='"write": true'):
        api.Bridge(_spec([tool]))


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_every_mutating_method_needs_the_flag(method):
    tool = _get_tool(name="t", method=method, path="/orders/{order_no}")
    with pytest.raises(api.SpecError):
        api.Bridge(_spec([tool]))
    ok = api.Bridge(_spec([_get_tool(name="t", method=method, path="/orders/{order_no}", write=True)]))
    assert ok.tools["t"].write is True


def test_check_mode_names_the_write_tools(capsys, tmp_path, token):
    spec = _spec(
        [
            _get_tool(),
            _get_tool(
                name="corp_order_close",
                method="POST",
                path="/orders/{order_no}/close",
                write=True,
            ),
        ]
    )
    path = tmp_path / "api.json"
    path.write_text(json.dumps(spec), encoding="utf-8")
    assert api.main(["--spec", str(path), "--check"]) == 0
    out = capsys.readouterr().out
    assert "corp_order_close" in out
    assert "requires_approval" in out, "--check 要提醒把写工具挂到需审批的 server 上"


# -- 守卫 5：凭据只从环境变量取 ---------------------------------------------------
def test_authorization_header_in_spec_is_refused():
    """这份 spec 会进版本库。凭据写在里面就是提交一次泄露。"""
    with pytest.raises(api.SpecError, match="auth.token_env"):
        api.Bridge(
            _spec(
                [_get_tool()],
                defaults={"headers": {"Authorization": "Bearer hardcoded"}},
            )
        )


@pytest.mark.parametrize("header", ["authorization", "Cookie", "Proxy-Authorization"])
def test_credential_headers_are_refused_case_insensitively(header):
    with pytest.raises(api.SpecError):
        api.Bridge(_spec([_get_tool()], defaults={"headers": {header: "x"}}))


def test_missing_credential_env_fails_at_startup(monkeypatch):
    """启动就失败，好过每次调用回 401 让模型以为是"这条记录没权限"。"""
    monkeypatch.delenv("CORP_API_TOKEN", raising=False)
    with pytest.raises(api.SpecError, match="CORP_API_TOKEN"):
        api.Bridge(_spec([_get_tool()], auth={"type": "bearer", "token_env": "CORP_API_TOKEN"}))


def test_bearer_token_reaches_the_request(token):
    seen: list[httpx.Request] = []
    bridge = _bridge(
        _spec([_get_tool()], auth={"type": "bearer", "token_env": "CORP_API_TOKEN"}),
        handler=_seen(seen),
    )
    _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert seen[0].headers["authorization"] == f"Bearer {token}"


def test_basic_auth_builds_the_header(monkeypatch):
    monkeypatch.setenv("CORP_USER", "svc")
    monkeypatch.setenv("CORP_PASS", "pw")
    bridge = api.Bridge(
        _spec(
            [_get_tool()],
            auth={"type": "basic", "user_env": "CORP_USER", "password_env": "CORP_PASS"},
        )
    )
    assert bridge.auth.value == "Basic c3ZjOnB3"


def test_custom_header_auth(monkeypatch):
    monkeypatch.setenv("CORP_API_TOKEN", "abc")
    bridge = api.Bridge(
        _spec(
            [_get_tool()],
            auth={"type": "header", "header": "X-Corp-Token", "token_env": "CORP_API_TOKEN"},
        )
    )
    assert bridge.auth.header == "X-Corp-Token"
    assert bridge.auth.value == "abc"


def test_unknown_auth_type_is_refused():
    with pytest.raises(api.SpecError, match="auth.type"):
        api.Bridge(_spec([_get_tool()], auth={"type": "magic"}))


# -- 守卫 6：不允许关 TLS 校验 ----------------------------------------------------
def test_verify_false_is_refused():
    with pytest.raises(api.SpecError, match="ca_bundle"):
        api.Bridge(_spec([_get_tool()], defaults={"verify": False}))


def test_ca_bundle_must_exist(tmp_path):
    with pytest.raises(api.SpecError, match="找不到"):
        api.Bridge(_spec([_get_tool()], defaults={"ca_bundle": str(tmp_path / "nope.pem")}))


def test_ca_bundle_is_used_when_present(tmp_path):
    ca = tmp_path / "corp.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    bridge = api.Bridge(_spec([_get_tool()], defaults={"ca_bundle": str(ca)}))
    assert bridge.verify == str(ca)


# -- 参数校验 -------------------------------------------------------------------
def test_undeclared_argument_is_refused_not_ignored(token):
    bridge = _bridge(_spec([_get_tool()]), handler=_seen([]))
    res = _call(bridge, "corp_order_get", {"order_no": "SO1", "admin": True})
    assert res["ok"] is False and "未声明的参数" in res["error"]


def test_missing_required_argument(token):
    bridge = _bridge(_spec([_get_tool()]), handler=_seen([]))
    res = _call(bridge, "corp_order_get", {})
    assert res["ok"] is False and "order_no" in res["error"]


def test_boolean_does_not_pass_as_integer(token):
    tool = _get_tool(
        name="t",
        path="/orders",
        params=[{"name": "limit", "type": "integer", "in": "query"}],
    )
    bridge = _bridge(_spec([tool]), handler=_seen([]))
    res = _call(bridge, "t", {"limit": True})
    assert res["ok"] is False and "boolean" in res["error"]


def test_enum_is_enforced(token):
    tool = _get_tool(
        name="t",
        path="/orders",
        params=[
            {"name": "status", "type": "string", "in": "query", "enum": ["open", "closed"]}
        ],
    )
    bridge = _bridge(_spec([tool]), handler=_seen([]))
    res = _call(bridge, "t", {"status": "deleted"})
    assert res["ok"] is False and "只能取" in res["error"]


def test_query_and_body_go_where_declared(token):
    seen: list[httpx.Request] = []
    tool = _get_tool(
        name="t",
        method="POST",
        path="/orders/{order_no}/close",
        write=True,
        params=[
            {"name": "order_no", "type": "string", "in": "path", "required": True},
            {"name": "notify", "type": "boolean", "in": "query"},
            {"name": "reason", "type": "string", "in": "body", "required": True},
        ],
    )
    bridge = _bridge(_spec([tool]), handler=_seen(seen))
    _call(bridge, "t", {"order_no": "SO1", "notify": True, "reason": "重复下单"})
    request = seen[0]
    assert request.url.path.endswith("/orders/SO1/close")
    assert request.url.params["notify"] == "true"
    assert json.loads(request.content) == {"reason": "重复下单"}


def test_unknown_tool_name(token):
    bridge = _bridge(_spec([_get_tool()]), handler=_seen([]))
    assert _call(bridge, "nope", {})["ok"] is False


# -- spec 结构校验 ---------------------------------------------------------------
def test_path_template_and_declared_path_params_must_match():
    """模板里打错一个字，URL 里就会留下字面量 {order_no} 然后 404。"""
    tool = _get_tool(path="/orders/{orderno}")
    with pytest.raises(api.SpecError, match="不一致"):
        api.Bridge(_spec([tool]))


def test_declared_path_param_not_in_template_is_refused():
    tool = _get_tool(
        path="/orders",
        params=[{"name": "order_no", "type": "string", "in": "path", "required": True}],
    )
    with pytest.raises(api.SpecError, match="不一致"):
        api.Bridge(_spec([tool]))


def test_path_param_must_be_required():
    tool = _get_tool(
        params=[{"name": "order_no", "type": "string", "in": "path", "required": False}]
    )
    with pytest.raises(api.SpecError, match="required"):
        api.Bridge(_spec([tool]))


def test_duplicate_tool_names_are_refused():
    with pytest.raises(api.SpecError, match="重复"):
        api.Bridge(_spec([_get_tool(), _get_tool()]))


def test_base_url_must_be_absolute_http():
    with pytest.raises(api.SpecError, match="base_url"):
        api.Bridge({"base_url": "erp.corp.example.com", "tools": [_get_tool()]})


def test_empty_tools_is_refused():
    with pytest.raises(api.SpecError, match="tools"):
        api.Bridge({"base_url": BASE, "tools": []})


def test_bad_tool_name_characters():
    with pytest.raises(api.SpecError, match="工具名"):
        api.Bridge(_spec([_get_tool(name="corp order get")]))


def test_bad_redact_regex():
    with pytest.raises(api.SpecError, match="正则"):
        api.Bridge(_spec([_get_tool()], defaults={"redact": ["("]}))


def test_load_spec_reports_bad_json(tmp_path):
    path = tmp_path / "api.json"
    path.write_text("{ not json", encoding="utf-8")
    with pytest.raises(api.SpecError, match="合法 JSON"):
        api.load_spec(path)


def test_main_returns_2_on_spec_error(tmp_path, capsys):
    path = tmp_path / "api.json"
    path.write_text(json.dumps({"base_url": BASE, "tools": []}), encoding="utf-8")
    assert api.main(["--spec", str(path), "--check"]) == 2
    assert "[spec 错误]" in capsys.readouterr().err


# -- 错误与输出处理 --------------------------------------------------------------
def test_401_says_permission_not_outage(token):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "unauthorized"})

    bridge = _bridge(_spec([_get_tool()]), handler=handler)
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert res["ok"] is False and res["status"] == 401
    assert "无权" in res["error"] and "重试不会成功" in res["error"]


def test_500_body_is_clipped_and_scrubbed(token):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text='{"token": "leaked-abc"} ' + "x" * 5000)

    bridge = _bridge(
        _spec([_get_tool()], defaults={"redact": ['"token"\\s*:\\s*"[^"]*"']}),
        handler=handler,
    )
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert "leaked-abc" not in res["error"]
    assert len(res["error"]) < 1200


def test_output_is_clipped_at_max_output(token):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"note": "y" * 5000})

    bridge = _bridge(_spec([_get_tool(max_output=200)]), handler=handler)
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert "已截断" in res["data"] and len(res["data"]) < 400


def test_redaction_applies_to_successful_bodies(token):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"phone": "13800138000", "status": "ok"})

    bridge = _bridge(
        _spec([_get_tool()], defaults={"redact": ['"phone"\\s*:\\s*"[^"]*"']}),
        handler=handler,
    )
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert "13800138000" not in res["data"] and "已脱敏" in res["data"]


def test_non_json_response_comes_back_as_text(token):
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="plain body")

    bridge = _bridge(_spec([_get_tool()]), handler=handler)
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert res["ok"] is True and res["text"] == "plain body"


def test_timeout_is_reported_as_timeout(token):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ReadTimeout("too slow", request=request)

    bridge = _bridge(_spec([_get_tool(timeout=3)]), handler=handler)
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert res["ok"] is False and "超时（3s）" in res["error"]


def test_transport_error_is_scrubbed(token):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connect failed to s3cr3t-token@host", request=request)

    bridge = _bridge(
        _spec([_get_tool()], defaults={"redact": ["s3cr3t-token"]}), handler=handler
    )
    res = _call(bridge, "corp_order_get", {"order_no": "SO1"})
    assert res["ok"] is False and "s3cr3t-token" not in res["error"]


# -- 随包模板本身必须是合法的 -----------------------------------------------------
@pytest.mark.parametrize("name", ["erp-read.example.json", "erp-write.example.json"])
def test_shipped_examples_load(name, tmp_path, monkeypatch):
    """模板里 ca_bundle 指向 /opt/corp/…，本机没有；替换成临时文件后必须能加载。

    模板是给人照抄的，抄之前它得自己是对的。
    """
    monkeypatch.setenv("CORP_API_TOKEN", "x")
    raw = json.loads((TEMPLATE_DIR / name).read_text(encoding="utf-8"))
    ca = tmp_path / "ca.pem"
    ca.write_text("-----BEGIN CERTIFICATE-----\n", encoding="utf-8")
    raw["defaults"]["ca_bundle"] = str(ca)
    bridge = api.Bridge(raw)
    assert bridge.tools


def test_read_example_declares_no_write_tools(tmp_path, monkeypatch):
    """读的那份 spec 里出现写工具，就说明读写拆分被破坏了。"""
    monkeypatch.setenv("CORP_API_TOKEN", "x")
    raw = json.loads((TEMPLATE_DIR / "erp-read.example.json").read_text(encoding="utf-8"))
    ca = tmp_path / "ca.pem"
    ca.write_text("x", encoding="utf-8")
    raw["defaults"]["ca_bundle"] = str(ca)
    bridge = api.Bridge(raw)
    assert [t.name for t in bridge.tools.values() if t.write] == []


def test_write_example_declares_only_write_tools(tmp_path, monkeypatch):
    monkeypatch.setenv("CORP_API_TOKEN", "x")
    raw = json.loads((TEMPLATE_DIR / "erp-write.example.json").read_text(encoding="utf-8"))
    ca = tmp_path / "ca.pem"
    ca.write_text("x", encoding="utf-8")
    raw["defaults"]["ca_bundle"] = str(ca)
    bridge = api.Bridge(raw)
    assert all(t.write for t in bridge.tools.values())


def test_every_shipped_tool_declares_a_field_whitelist(tmp_path, monkeypatch):
    """模板要示范好习惯：内网响应默认不该整包回流。"""
    monkeypatch.setenv("CORP_API_TOKEN", "x")
    ca = tmp_path / "ca.pem"
    ca.write_text("x", encoding="utf-8")
    for name in ("erp-read.example.json", "erp-write.example.json"):
        raw = json.loads((TEMPLATE_DIR / name).read_text(encoding="utf-8"))
        raw["defaults"]["ca_bundle"] = str(ca)
        for tool in api.Bridge(raw).tools.values():
            assert tool.fields, f"{name} 的 {tool.name} 没有 fields 白名单"


# -- MCP 面 ---------------------------------------------------------------------
def test_tool_schema_forbids_additional_properties():
    bridge = api.Bridge(_spec([_get_tool()]))
    schema = bridge.tools["corp_order_get"].schema()
    assert schema["additionalProperties"] is False
    assert schema["required"] == ["order_no"]
