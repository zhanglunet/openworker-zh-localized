#!/usr/bin/env python3
"""企业内部系统 HTTP API → MCP 工具桥。

企业要接的第一个内部系统，十有八九是一套 HTTP/REST 接口：ERP、工单、HR、审批流。
接它有两条路，这是推荐的那条（另一条见 docs/enterprise/CONNECTOR_GUIDE.md）：

不动上游任何文件，用一份 api.json 声明「哪些接口、各自什么参数、返回哪些字段」，
桥自己生成 MCP 工具。换一个内网系统只改 JSON。

用法（写进 <state-dir>/mcp.json）：

    {
      "mcpServers": {
        "corp-erp": {
          "command": "python3",
          "args": ["/opt/corp/openworker/corp-api/server.py",
                   "--spec", "/opt/corp/openworker/corp-api/erp-read.json",
                   "--name", "corp-erp"],
          "env": {"CORP_API_TOKEN": "${CORP_API_TOKEN}"},
          "requires_approval": false
        },
        "corp-erp-write": {
          "command": "python3",
          "args": ["/opt/corp/openworker/corp-api/server.py",
                   "--spec", "/opt/corp/openworker/corp-api/erp-write.json",
                   "--name", "corp-erp-write"],
          "env": {"CORP_API_TOKEN": "${CORP_API_TOKEN}"},
          "requires_approval": true
        }
      }
    }

读写为什么要拆成两个 server：OpenWorker 的 `requires_approval` 是 **server 级**的
（coworker/mcp/config.py），不是工具级。混在一个 server 里只有两种结局——要么查个订单
也弹审批框，弹到用户开始无脑点「同意」；要么关掉审批，连关单、改单一起放行。拆开之后
读的那半永不打扰，写的那半永远拦一道。

安全边界（每条都有测试钉着，见 tests/test_corp_api_server.py）：
- 路径参数逐段百分号转义，且拼完的 URL 必须仍在 base_url 之下 —— `{id}` 传
  `../../admin/users` 到不了别的接口
- **不跟随重定向**：内网系统一个 302 就能把 Authorization 头送到别的 host 去
- 响应按 `fields` 白名单裁剪：内网记录里的身份证号、薪资、手机号不该整包进模型上下文
- 非 GET/HEAD 的接口必须显式声明 `"write": true`，否则 spec 加载即失败 —— 哪些工具会
  改数据必须是配置里看得见的事实，不是读代码猜出来的
- 凭据只从环境变量取；spec 里写死 Authorization 头会被拒绝加载
- 不允许关 TLS 校验；自签证书请配 `ca_bundle`
- 超时、输出截断、输出脱敏
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import sys
from pathlib import Path
from posixpath import normpath
from typing import Any, Optional
from urllib.parse import quote, urlsplit, urlunsplit

DEFAULT_TIMEOUT = 30
DEFAULT_MAX_OUTPUT = 20_000

_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}
_LOCATIONS = ("path", "query", "body")
_METHODS = ("GET", "HEAD", "POST", "PUT", "PATCH", "DELETE")
_SAFE_METHODS = ("GET", "HEAD")
_PATH_TOKEN = re.compile(r"\{([a-zA-Z0-9_]+)\}")


class SpecError(Exception):
    """api.json 本身有问题——启动即失败，不要带着半个配置跑起来。"""


# -- 参数 ----------------------------------------------------------------------
class Param:
    def __init__(self, raw: dict, tool: str):
        self.name = _req_str(raw, "name")
        self.type = raw.get("type", "string")
        if self.type not in _TYPES:
            raise SpecError(f"{tool}.{self.name}.type 必须是 {sorted(_TYPES)} 之一")
        self.location = raw.get("in", "query")
        if self.location not in _LOCATIONS:
            raise SpecError(
                f"{tool}.{self.name}.in 必须是 {list(_LOCATIONS)} 之一，收到 {self.location!r}"
            )
        self.description = raw.get("description", "")
        self.required = bool(raw.get("required"))
        if self.location == "path" and not self.required:
            # 路径参数缺了就没法拼出 URL；允许它可选只会让错误延后到运行时
            raise SpecError(f"{tool}.{self.name} 是路径参数，必须 required")
        self.enum = raw.get("enum")
        if self.enum is not None and (not isinstance(self.enum, list) or not self.enum):
            raise SpecError(f"{tool}.{self.name}.enum 必须是非空数组")

    def schema(self) -> dict:
        out: dict[str, Any] = {"type": self.type}
        if self.description:
            out["description"] = self.description
        if self.enum:
            out["enum"] = list(self.enum)
        return out

    def coerce(self, value: Any) -> Any:
        expected = _TYPES[self.type]
        # bool 是 int 的子类，别让 True 混过 integer 校验
        if self.type != "boolean" and isinstance(value, bool):
            raise ValueError(f"{self.name} 需要 {self.type}，收到 boolean")
        if not isinstance(value, expected):
            raise ValueError(
                f"{self.name} 需要 {self.type}，收到 {type(value).__name__}"
            )
        if self.enum is not None and value not in self.enum:
            raise ValueError(f"{self.name} 只能取 {self.enum} 之一，收到 {value!r}")
        return value


# -- 接口 ----------------------------------------------------------------------
class Endpoint:
    def __init__(self, raw: dict, defaults: dict):
        self.name = _req_str(raw, "name")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", self.name):
            raise SpecError(
                f"工具名 {self.name!r} 只能是字母/数字/下划线/连字符，且不超过 64 字符"
            )
        self.description = _req_str(raw, "description")
        self.method = str(raw.get("method", "GET")).upper()
        if self.method not in _METHODS:
            raise SpecError(f"{self.name}.method 必须是 {list(_METHODS)} 之一")
        self.path = _req_str(raw, "path")
        if not self.path.startswith("/"):
            raise SpecError(f"{self.name}.path 必须以 / 开头，收到 {self.path!r}")
        self.params = [Param(p, self.name) for p in raw.get("params") or []]
        names = [p.name for p in self.params]
        if len(names) != len(set(names)):
            raise SpecError(f"{self.name} 的参数名有重复：{names}")

        declared = {p.name for p in self.params if p.location == "path"}
        in_template = set(_PATH_TOKEN.findall(self.path))
        if declared != in_template:
            # 模板里打错一个字，URL 里就会留下字面量 {order_no} 然后 404;
            # 声明了却没用上的路径参数同样是配置错误
            raise SpecError(
                f"{self.name}：path 模板里的占位符 {sorted(in_template)} 与声明的路径参数 "
                f"{sorted(declared)} 不一致"
            )

        self.write = bool(raw.get("write"))
        if self.method not in _SAFE_METHODS and not self.write:
            raise SpecError(
                f"{self.name} 是 {self.method}，必须显式声明 \"write\": true。"
                "哪些工具会改数据，要在配置里一眼看得见（也提醒你把它放进"
                "requires_approval 的那个 server）"
            )
        fields = raw.get("fields")
        if fields is not None and (
            not isinstance(fields, list)
            or not fields
            or not all(isinstance(f, str) and f.strip() for f in fields)
        ):
            raise SpecError(f"{self.name}.fields 必须是非空字符串数组（或者干脆不写）")
        self.fields = [f.strip() for f in fields] if fields else None
        self.timeout = int(raw.get("timeout") or defaults.get("timeout") or DEFAULT_TIMEOUT)
        self.max_output = int(
            raw.get("max_output") or defaults.get("max_output") or DEFAULT_MAX_OUTPUT
        )

    def schema(self) -> dict:
        props, required = {}, []
        for p in self.params:
            props[p.name] = p.schema()
            if p.required:
                required.append(p.name)
        return {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False,
        }

    def bind(self, args: dict) -> tuple[str, dict, dict]:
        """声明的参数 → (path, query, body)。未声明的参数一律拒绝，不是忽略——静默忽略
        会让调用方以为参数生效了。"""
        unknown = set(args) - {p.name for p in self.params}
        if unknown:
            raise ValueError(f"未声明的参数：{sorted(unknown)}")
        path, query, body = self.path, {}, {}
        for p in self.params:
            if p.name not in args or args[p.name] is None:
                if p.required:
                    raise ValueError(f"缺少必填参数 {p.name}")
                continue
            value = p.coerce(args[p.name])
            if p.location == "path":
                # safe="" —— 斜杠也要转义。否则 order_no="../../admin/users" 就是一次
                # 换接口的越权调用，而不是一个查不到的订单号。
                path = path.replace("{" + p.name + "}", quote(str(value), safe=""))
            elif p.location == "query":
                query[p.name] = value
            else:
                body[p.name] = value
        return path, query, body


# -- 认证 ----------------------------------------------------------------------
class Auth:
    def __init__(self, raw: Optional[dict]):
        raw = raw or {"type": "none"}
        if not isinstance(raw, dict):
            raise SpecError("auth 必须是对象")
        self.type = str(raw.get("type", "none")).lower()
        self.header = raw.get("header") or "Authorization"
        if self.type == "none":
            self.value = None
            return
        if self.type in ("bearer", "header"):
            env = _req_str(raw, "token_env")
            self.value = _require_env(env)
            if self.type == "bearer":
                self.header, self.value = "Authorization", f"Bearer {self.value}"
        elif self.type == "basic":
            import base64

            user = _require_env(_req_str(raw, "user_env"))
            password = _require_env(_req_str(raw, "password_env"))
            token = base64.b64encode(f"{user}:{password}".encode()).decode()
            self.header, self.value = "Authorization", f"Basic {token}"
        else:
            raise SpecError(
                f"auth.type 只支持 none / bearer / header / basic，收到 {self.type!r}"
            )

    def apply(self, headers: dict[str, str]) -> dict[str, str]:
        if self.value:
            headers = {**headers, self.header: self.value}
        return headers


def _require_env(name: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        # 启动就失败，好过每次调用回一个 401 让模型以为是"这条记录没权限"
        raise SpecError(f"环境变量 {name} 没有设置（凭据只从环境变量取，不写进 spec）")
    return value


def _req_str(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"缺少必填字段 {key}（或不是非空字符串）")
    return value.strip()


# -- 响应字段白名单 -------------------------------------------------------------
def _field_tree(paths: list[str]) -> dict:
    root: dict = {}
    for path in paths:
        node = root
        for seg in path.split("."):
            node = node.setdefault(seg, {})
    return root


def pick_fields(data: Any, tree: dict) -> Any:
    """按白名单树裁剪响应。列表逐元素套用，所以 `results.order_no` 能裁剪
    `{"results": [{...}, {...}]}`。"""
    if not tree:
        return data
    if isinstance(data, list):
        return [pick_fields(item, tree) for item in data]
    if isinstance(data, dict):
        return {k: pick_fields(data[k], sub) for k, sub in tree.items() if k in data}
    return data


# -- 桥 ------------------------------------------------------------------------
class Bridge:
    def __init__(self, spec: dict):
        if not isinstance(spec, dict):
            raise SpecError("spec 顶层必须是对象")
        base = _req_str(spec, "base_url")
        parts = urlsplit(base)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise SpecError(f"base_url 必须是 http(s):// 开头的绝对地址，收到 {base!r}")
        self.base_url = base.rstrip("/")
        self.base_parts = urlsplit(self.base_url)

        defaults = spec.get("defaults") or {}
        if not isinstance(defaults, dict):
            raise SpecError("defaults 必须是对象")
        self.headers = {
            str(k): str(v) for k, v in (defaults.get("headers") or {}).items()
        }
        for key in self.headers:
            if key.lower() in ("authorization", "proxy-authorization", "cookie"):
                raise SpecError(
                    f"不要在 defaults.headers 里写 {key} —— 这份 spec 会进版本库。"
                    "凭据请用 auth.token_env 从环境变量取"
                )
        self.auth = Auth(spec.get("auth"))

        if defaults.get("verify") is False:
            raise SpecError(
                "不允许 verify=false。内网自签证书请把企业根证书路径写进 "
                "defaults.ca_bundle —— 关掉校验等于把内网流量交给任何能插进链路的人"
            )
        ca = defaults.get("ca_bundle")
        if ca is not None:
            ca_path = Path(str(ca)).expanduser()
            if not ca_path.is_file():
                raise SpecError(f"ca_bundle 找不到：{ca_path}")
            self.verify: Any = str(ca_path)
        else:
            self.verify = True

        self.redact = []
        for pattern in defaults.get("redact") or []:
            try:
                self.redact.append(re.compile(pattern))
            except re.error as exc:
                raise SpecError(f"redact 正则 {pattern!r} 无效：{exc}") from exc

        raw_tools = spec.get("tools")
        if not isinstance(raw_tools, list) or not raw_tools:
            raise SpecError('spec 必须有非空的 "tools" 数组')
        self.tools: dict[str, Endpoint] = {}
        for raw in raw_tools:
            if not isinstance(raw, dict):
                raise SpecError("tools 的每一项都必须是对象")
            endpoint = Endpoint(raw, defaults)
            if endpoint.name in self.tools:
                raise SpecError(f"工具名重复：{endpoint.name}")
            self.tools[endpoint.name] = endpoint

    # -- 单次调用 --------------------------------------------------------------
    def scrub(self, text: str) -> str:
        for pattern in self.redact:
            text = pattern.sub("«已脱敏»", text)
        return text

    def clip(self, text: str, limit: int) -> str:
        if len(text) > limit:
            return f"{text[:limit]}\n…（输出超过 {limit} 字符，已截断）"
        return text

    def build_url(self, endpoint: Endpoint, path: str) -> str:
        """纵深防御：即使某天转义被改坏，拼出来的地址仍必须落在 base_url 之下。

        比较前**先归一化路径**——字符串前缀比对在这里是假的守卫：
        `https://host/api/v2` + `/../../admin` 前缀完全匹配，解析出来却是 `/admin`。
        （这条是写完测试才发现的：第一版就是纯前缀比对，用例直接把它打红了。）
        """
        parts = urlsplit(self.base_url + path)
        norm = normpath(parts.path)
        if parts.path.endswith("/") and not norm.endswith("/"):
            norm += "/"  # normpath 会吃掉尾斜杠，别让它把 /orders/ 变成 /orders
        base_path = self.base_parts.path.rstrip("/")
        same_host = (parts.scheme, parts.netloc) == (
            self.base_parts.scheme,
            self.base_parts.netloc,
        )
        under_base = norm == base_path or norm.startswith(base_path + "/")
        if not (same_host and under_base):
            raise ValueError(
                f"{endpoint.name}：拼出的地址越出 base_url（{parts.netloc}{norm}）"
            )
        return urlunsplit(
            (parts.scheme, parts.netloc, norm, parts.query, parts.fragment)
        )

    async def call(self, name: str, args: dict) -> dict:
        endpoint = self.tools.get(name)
        if endpoint is None:
            return {"ok": False, "error": f"未声明的工具：{name}"}
        try:
            path, query, body = endpoint.bind(args or {})
            url = self.build_url(endpoint, path)
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}

        import httpx

        headers = self.auth.apply({**self.headers, "Accept": "application/json"})
        try:
            async with httpx.AsyncClient(
                verify=self.verify,
                timeout=endpoint.timeout,
                # 一个 302 就能把 Authorization 头带去另一个 host。内部系统的重定向
                # 通常是登录页——跟过去只会把凭据送给它，还拿回一坨 HTML。
                follow_redirects=False,
                transport=self._transport,
            ) as client:
                resp = await client.request(
                    endpoint.method,
                    url,
                    params=query or None,
                    json=body or None,
                    headers=headers,
                )
        except httpx.TimeoutException:
            return {"ok": False, "error": f"超时（{endpoint.timeout}s）：{endpoint.name}"}
        except httpx.HTTPError as exc:
            return {"ok": False, "error": self.scrub(f"请求失败：{exc}")}

        return self._result(endpoint, resp)

    _transport = None  # 测试用注入点；生产为 None，httpx 走默认传输

    def _result(self, endpoint: Endpoint, resp: Any) -> dict:
        if 300 <= resp.status_code < 400:
            location = resp.headers.get("location", "")
            host = urlsplit(location).netloc or "（未给 Location）"
            return {
                "ok": False,
                "status": resp.status_code,
                "error": (
                    f"接口返回了重定向（→ {host}），本桥不跟随：跟过去会把凭据发给那个地址。"
                    "如果这是正常行为，请把 base_url 直接指向最终地址"
                ),
            }
        if resp.status_code in (401, 403):
            return {
                "ok": False,
                "status": resp.status_code,
                "error": "内部系统拒绝了这次调用：凭据无效或当前账号无权访问该资源"
                "（不是服务故障，重试不会成功）",
            }
        text = resp.text or ""
        if resp.status_code >= 400:
            return {
                "ok": False,
                "status": resp.status_code,
                "error": self.clip(self.scrub(text), 1000) or f"HTTP {resp.status_code}",
            }
        try:
            data = resp.json()
        except Exception:
            return {
                "ok": True,
                "status": resp.status_code,
                "text": self.clip(self.scrub(text), endpoint.max_output),
            }
        if endpoint.fields:
            data = pick_fields(data, _field_tree(endpoint.fields))
        rendered = self.clip(
            self.scrub(json.dumps(data, ensure_ascii=False)), endpoint.max_output
        )
        return {"ok": True, "status": resp.status_code, "data": rendered}


def load_spec(path: Path) -> Bridge:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SpecError(f"找不到 spec：{path}") from exc
    except json.JSONDecodeError as exc:
        raise SpecError(f"spec 不是合法 JSON：{exc}") from exc
    return Bridge(raw)


async def serve(bridge: Bridge, name: str) -> None:
    try:
        from mcp.server import Server
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool as MCPTool
    except ImportError:  # pragma: no cover - 依赖缺失时给中文提示而不是 traceback
        sys.stderr.write("需要 mcp 包：pip install 'mcp>=1.1,<2'\n")
        raise SystemExit(2)

    server = Server(name)

    @server.list_tools()
    async def list_tools() -> list:
        return [
            MCPTool(name=t.name, description=t.description, inputSchema=t.schema())
            for t in bridge.tools.values()
        ]

    @server.call_tool()
    async def call_tool(tool_name: str, arguments: dict) -> list:
        result = await bridge.call(tool_name, arguments or {})
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async with stdio_server() as (read, write):
        await server.run(read, write, server.create_initialization_options())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="把企业内部系统的 HTTP 接口暴露成 MCP 工具")
    ap.add_argument("--spec", required=True, help="api.json 路径")
    ap.add_argument("--name", default="corp-api", help="MCP server 名（默认 corp-api）")
    ap.add_argument(
        "--check", action="store_true", help="只校验 spec 并列出工具，不启动服务"
    )
    args = ap.parse_args(argv)

    try:
        bridge = load_spec(Path(args.spec).expanduser())
    except SpecError as exc:
        sys.stderr.write(f"[spec 错误] {exc}\n")
        return 2

    if args.check:
        writes = [t.name for t in bridge.tools.values() if t.write]
        print(f"spec 合法，base_url={bridge.base_url}，共 {len(bridge.tools)} 个工具：")
        for tool in bridge.tools.values():
            required = [p.name for p in tool.params if p.required]
            mark = "写" if tool.write else "读"
            fields = f" 字段白名单={len(tool.fields)} 项" if tool.fields else " 字段白名单=无"
            print(f"  · [{mark}] {tool.name}  {tool.method} {tool.path}  必填={required or '无'}{fields}")
        if writes:
            print(
                f"\n注意：本 spec 含 {len(writes)} 个写工具（{', '.join(writes)}）——"
                "请把它挂在 requires_approval=true 的 MCP server 上。"
            )
        return 0

    asyncio.run(serve(bridge, args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
