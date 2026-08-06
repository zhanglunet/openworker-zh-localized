#!/usr/bin/env python3
"""企业 CLI → MCP 桥：把一个命令行工具的若干子命令，声明成 MCP 工具。

为什么不直接放行 shell：把 `corp-cli` 加进 allowed_commands 等于把整个 CLI 的全部
子命令、全部参数都交出去——包括 `delete`、`--force`、以及你没想到的那些。本桥反过来做：
**只有白名单里显式声明的子命令能被调用，参数逐个校验**，其余一律拒绝。

而且企业每接一个 CLI 就手写一个 MCP server 是没必要的重复劳动。这里用一份 tools.json
描述「哪些子命令、各自什么参数」，桥自己生成 MCP 工具定义。

用法（写进 <state-dir>/mcp.json）：

    {
      "mcpServers": {
        "corp-cli": {
          "command": "python3",
          "args": ["/opt/corp/openworker/cli-bridge/server.py",
                   "--spec", "/opt/corp/openworker/cli-bridge/tools.json"],
          "env": {"CORP_TOKEN": "${CORP_TOKEN}"},
          "requires_approval": true
        }
      }
    }

安全边界（都有测试钉着）：
- 永不经过 shell：subprocess 直接传 argv 列表，`;`、`|`、`$(…)` 只会成为普通字符串实参
- 只放行 spec 里声明的子命令；参数名、类型、enum 取值逐个校验
- 每次调用有超时；输出超长截断（模型上下文不该被一次 CLI 输出撑爆）
- 输出按 spec 的 redact 正则脱敏（token/密钥不该回流进对话与日志）
- 工作目录、环境变量白名单都由 spec 决定，不继承调用方的整个环境
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import shutil
import sys
from pathlib import Path
from typing import Any, Optional

DEFAULT_TIMEOUT = 60
DEFAULT_MAX_OUTPUT = 20_000

_TYPES = {"string": str, "integer": int, "number": (int, float), "boolean": bool}


class SpecError(Exception):
    """spec.json 本身有问题——启动即失败，不要带着半个配置跑起来。"""


class Tool:
    def __init__(self, raw: dict, defaults: dict):
        self.name = _req_str(raw, "name")
        if not re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", self.name):
            raise SpecError(f"工具名 {self.name!r} 只能是字母/数字/下划线/连字符，且不超过 64 字符")
        self.description = _req_str(raw, "description")
        argv = raw.get("argv")
        if not isinstance(argv, list) or not argv or not all(isinstance(a, str) for a in argv):
            raise SpecError(f"{self.name}.argv 必须是非空字符串数组，如 [\"corp-cli\", \"ticket\", \"create\"]")
        self.argv = argv
        self.params = [Param(p, self.name) for p in raw.get("params") or []]
        self.timeout = int(raw.get("timeout") or defaults.get("timeout") or DEFAULT_TIMEOUT)
        self.max_output = int(
            raw.get("max_output") or defaults.get("max_output") or DEFAULT_MAX_OUTPUT
        )
        self.cwd = raw.get("cwd") or defaults.get("cwd")

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

    def build_argv(self, args: dict) -> list[str]:
        """声明的参数 → argv。未声明的参数一律拒绝，不是忽略——静默忽略会让调用方
        以为参数生效了。"""
        unknown = set(args) - {p.name for p in self.params}
        if unknown:
            raise ValueError(f"未声明的参数：{sorted(unknown)}")
        argv = list(self.argv)
        for p in self.params:
            if p.name not in args or args[p.name] is None:
                if p.required:
                    raise ValueError(f"缺少必填参数 {p.name}")
                continue
            argv.extend(p.render(args[p.name]))
        return argv


class Param:
    def __init__(self, raw: dict, tool: str):
        self.name = _req_str(raw, "name")
        self.type = raw.get("type", "string")
        if self.type not in _TYPES:
            raise SpecError(f"{tool}.{self.name}.type 必须是 {sorted(_TYPES)} 之一")
        self.description = raw.get("description", "")
        self.required = bool(raw.get("required"))
        self.flag = raw.get("flag")  # 如 "--title"；不写则作为位置参数
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

    def render(self, value: Any) -> list[str]:
        expected = _TYPES[self.type]
        # bool 是 int 的子类，别让 True 混过 integer 校验
        if self.type != "boolean" and isinstance(value, bool):
            raise ValueError(f"{self.name} 需要 {self.type}，收到 boolean")
        if not isinstance(value, expected):
            raise ValueError(f"{self.name} 需要 {self.type}，收到 {type(value).__name__}")
        if self.enum is not None and value not in self.enum:
            raise ValueError(f"{self.name} 只能取 {self.enum} 之一，收到 {value!r}")
        if self.type == "boolean":
            # 布尔即开关：真则给出 flag，假则什么都不加
            if not self.flag:
                raise ValueError(f"{self.name} 是 boolean，必须声明 flag")
            return [self.flag] if value else []
        text = str(value)
        return [self.flag, text] if self.flag else [text]


def _req_str(raw: dict, key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SpecError(f"缺少必填字段 {key}（或不是非空字符串）")
    return value.strip()


class Bridge:
    def __init__(self, spec: dict):
        if not isinstance(spec, dict):
            raise SpecError("spec 顶层必须是对象")
        defaults = spec.get("defaults") or {}
        if not isinstance(defaults, dict):
            raise SpecError("defaults 必须是对象")
        raw_tools = spec.get("tools")
        if not isinstance(raw_tools, list) or not raw_tools:
            raise SpecError('spec 必须有非空的 "tools" 数组')
        self.tools: dict[str, Tool] = {}
        for raw in raw_tools:
            if not isinstance(raw, dict):
                raise SpecError("tools 的每一项都必须是对象")
            tool = Tool(raw, defaults)
            if tool.name in self.tools:
                raise SpecError(f"工具名重复：{tool.name}")
            self.tools[tool.name] = tool
        # 只把白名单里的环境变量传给子进程：默认不继承整个环境，免得把无关凭据带进 CLI。
        self.env_passthrough = [
            e for e in (defaults.get("env_passthrough") or []) if isinstance(e, str)
        ]
        self.redact = []
        for pattern in defaults.get("redact") or []:
            try:
                self.redact.append(re.compile(pattern))
            except re.error as exc:
                raise SpecError(f"redact 正则 {pattern!r} 无效：{exc}") from exc

    def child_env(self) -> dict[str, str]:
        env = {
            k: os.environ[k]
            for k in ("PATH", "HOME", "LANG", "LC_ALL", "SystemRoot", "TEMP", "TMP")
            if k in os.environ
        }
        for key in self.env_passthrough:
            if key in os.environ:
                env[key] = os.environ[key]
        return env

    def scrub(self, text: str) -> str:
        for pattern in self.redact:
            text = pattern.sub("«已脱敏»", text)
        return text

    async def call(self, name: str, args: dict) -> dict:
        tool = self.tools.get(name)
        if tool is None:
            return {"ok": False, "error": f"未声明的工具：{name}"}
        try:
            argv = tool.build_argv(args or {})
        except ValueError as exc:
            return {"ok": False, "error": str(exc)}
        if shutil.which(argv[0]) is None and not Path(argv[0]).is_file():
            return {"ok": False, "error": f"找不到可执行文件：{argv[0]}"}
        try:
            proc = await asyncio.create_subprocess_exec(
                *argv,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=tool.cwd or None,
                env=self.child_env(),
            )
        except OSError as exc:
            return {"ok": False, "error": f"启动失败：{exc}"}
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=tool.timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            return {"ok": False, "error": f"超时（{tool.timeout}s），已终止", "argv": argv[: len(tool.argv)]}

        def clip(raw: bytes) -> str:
            text = self.scrub(raw.decode("utf-8", "replace"))
            if len(text) > tool.max_output:
                head = text[: tool.max_output]
                return f"{head}\n…（输出超过 {tool.max_output} 字符，已截断）"
            return text

        return {
            "ok": proc.returncode == 0,
            "exit_code": proc.returncode,
            "stdout": clip(out),
            "stderr": clip(err),
        }


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
    ap = argparse.ArgumentParser(description="把企业 CLI 的若干子命令暴露成 MCP 工具")
    ap.add_argument("--spec", required=True, help="tools.json 路径")
    ap.add_argument("--name", default="corp-cli", help="MCP server 名（默认 corp-cli）")
    ap.add_argument("--check", action="store_true", help="只校验 spec 并列出工具，不启动服务")
    args = ap.parse_args(argv)

    try:
        bridge = load_spec(Path(args.spec).expanduser())
    except SpecError as exc:
        sys.stderr.write(f"[spec 错误] {exc}\n")
        return 2

    if args.check:
        print(f"spec 合法，共 {len(bridge.tools)} 个工具：")
        for tool in bridge.tools.values():
            required = [p.name for p in tool.params if p.required]
            print(f"  · {tool.name}  argv={' '.join(tool.argv)}  必填={required or '无'}")
        return 0

    asyncio.run(serve(bridge, args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
