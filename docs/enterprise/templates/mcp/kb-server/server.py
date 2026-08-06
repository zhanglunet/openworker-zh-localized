#!/usr/bin/env python3
"""企业知识库检索 MCP server（知识库 v2）。

v1（全局配置的 knowledge_roots）把知识目录只读挂进每个会话，够用且零成本，但有三件事做不到：

1. **知识库不是文件系统**。Confluence、语雀、自建 RAG 只有 HTTP 接口，挂不了盘。
2. **权限必须按人校验**。挂载是「这台机器上的这个用户能读的目录」，而合规要的是
   「这个人在知识库里有权看的内容」——两者不是一回事，后者只能由知识库自己回答。
3. **检索质量**。grep 在几万篇文档上既慢又只会字面匹配，知识库自己的检索（BM25/向量）
   才是该用的东西。

所以 v2 把知识库放在 MCP 后面：Agent 只能调 kb_search / kb_get，**拿不到文件系统访问权**，
每次调用带着调用方的凭据打到知识库，能看什么由知识库说了算。知识内容不进仓库、不进安装包。

两种后端，一份配置切换：

* `http`  —— 对接任何有搜索接口的知识库。响应字段用声明式映射，不必为每家写代码。
* `folder` —— 对着一棵文档目录做本地排序检索。给还没有检索服务的团队先用起来，
  也是本文件的可测形态。注意它与 v1 的区别：**不把目录挂给 Agent**，Agent 只拿得到
  检索结果，读不了任意文件。

用法（写进 <state-dir>/mcp.json）：

    {
      "mcpServers": {
        "corp-kb": {
          "command": "python3",
          "args": ["/opt/corp/openworker/kb-server/server.py",
                   "--config", "/opt/corp/openworker/kb-server/kb.json"],
          "env": {"CORP_KB_TOKEN": "${CORP_KB_TOKEN}"}
        }
      }
    }
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Optional

DEFAULT_LIMITS = {
    "max_results": 8,
    "snippet_chars": 500,
    "doc_chars": 20_000,
    "timeout": 15,
}

_ENV_REF = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")


class ConfigError(Exception):
    """配置有问题——启动即失败，不要带着半份配置跑起来。"""


def _resolve_env(value: str) -> str:
    """把 ${CORP_KB_TOKEN} 换成环境变量值，凭据不必写进配置文件。"""
    return _ENV_REF.sub(lambda m: os.environ.get(m.group(1), ""), value or "")


def _dig(data: Any, path: str) -> Any:
    """按 "data.items" 这样的点路径取值；取不到返回 None（而不是抛异常）。

    知识库的响应结构千奇百怪，映射写错是常态；这里返回 None 让上层给出可读的错误，
    比抛 KeyError 更有用。
    """
    cur = data
    for part in (path or "").split("."):
        if not part:
            continue
        if isinstance(cur, dict):
            cur = cur.get(part)
        elif isinstance(cur, list) and part.isdigit():
            idx = int(part)
            cur = cur[idx] if idx < len(cur) else None
        else:
            return None
        if cur is None:
            return None
    return cur


class Backend:
    def search(self, query: str, limit: int) -> dict:  # pragma: no cover - 接口
        raise NotImplementedError

    def get(self, doc_id: str) -> dict:  # pragma: no cover - 接口
        raise NotImplementedError


class HttpBackend(Backend):
    """对接任何有搜索接口的知识库。字段映射声明在配置里，不为每家写代码。"""

    def __init__(self, cfg: dict, limits: dict, redact: list):
        self.search_url = _req(cfg, "search_url")
        self.method = (cfg.get("method") or "GET").upper()
        if self.method not in ("GET", "POST"):
            raise ConfigError("http.method 只支持 GET 或 POST")
        self.query_param = cfg.get("query_param") or "q"
        self.limit_param = cfg.get("limit_param") or ""
        self.headers = {k: str(v) for k, v in (cfg.get("headers") or {}).items()}
        self.results_path = cfg.get("results_path") or ""
        self.fields = cfg.get("fields") or {}
        if not isinstance(self.fields, dict) or "title" not in self.fields:
            raise ConfigError('http.fields 至少要映射 "title"')
        self.doc_url = cfg.get("doc_url") or ""
        self.doc_field = cfg.get("doc_field") or "content"
        self.limits = limits
        self.redact = redact

    def _request(self, url: str, payload: Optional[dict] = None) -> Any:
        headers = {"Accept": "application/json"}
        for key, value in self.headers.items():
            headers[key] = _resolve_env(value)
        data = None
        if payload is not None and self.method == "POST":
            headers["Content-Type"] = "application/json"
            data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, headers=headers, method=self.method if data else "GET")
        with urllib.request.urlopen(req, timeout=self.limits["timeout"]) as resp:
            return json.loads(resp.read().decode("utf-8", "replace"))

    def search(self, query: str, limit: int) -> dict:
        try:
            if self.method == "POST":
                body = {self.query_param: query}
                if self.limit_param:
                    body[self.limit_param] = limit
                raw = self._request(self.search_url, body)
            else:
                params = {self.query_param: query}
                if self.limit_param:
                    params[self.limit_param] = str(limit)
                sep = "&" if "?" in self.search_url else "?"
                raw = self._request(f"{self.search_url}{sep}{urllib.parse.urlencode(params)}")
        except urllib.error.HTTPError as exc:
            # 401/403 是最常见的一类，且几乎总是「这个人无权看」而不是「服务坏了」——
            # 说清楚，别让人以为知识库宕机了。凭据本身绝不回显。
            hint = "（凭据无效或该用户无权访问）" if exc.code in (401, 403) else ""
            return {"error": f"知识库返回 HTTP {exc.code}{hint}"}
        except Exception as exc:  # noqa: BLE001
            return {"error": f"知识库不可达：{type(exc).__name__}"}

        rows = _dig(raw, self.results_path) if self.results_path else raw
        if not isinstance(rows, list):
            return {
                "error": "响应里找不到结果数组"
                + (f"（results_path={self.results_path!r}）" if self.results_path else "")
            }
        out = []
        for row in rows[:limit]:
            if not isinstance(row, dict):
                continue
            item = {}
            for name, path in self.fields.items():
                value = _dig(row, str(path))
                if value is not None:
                    item[name] = _clip(_scrub(str(value), self.redact), self.limits["snippet_chars"])
            if item:
                out.append(item)
        return {"ok": True, "count": len(out), "results": out}

    def get(self, doc_id: str) -> dict:
        if not self.doc_url:
            return {"error": "本知识库未配置 doc_url，只能检索不能取全文"}
        url = self.doc_url.replace("{id}", urllib.parse.quote(str(doc_id), safe=""))
        try:
            raw = self._request(url)
        except urllib.error.HTTPError as exc:
            hint = "（凭据无效或该用户无权访问）" if exc.code in (401, 403) else ""
            return {"error": f"知识库返回 HTTP {exc.code}{hint}"}
        except Exception as exc:  # noqa: BLE001
            return {"error": f"知识库不可达：{type(exc).__name__}"}
        body = _dig(raw, self.doc_field)
        if body is None:
            return {"error": f"响应里找不到正文字段 {self.doc_field!r}"}
        return {
            "ok": True,
            "id": doc_id,
            "content": _clip(_scrub(str(body), self.redact), self.limits["doc_chars"]),
        }


class FolderBackend(Backend):
    """对着一棵文档目录做本地排序检索。

    与 v1 的 knowledge_roots 的关键区别：**目录不挂给 Agent**。Agent 只能拿到检索结果，
    没有文件系统访问权——想读哪篇得先搜到它。适合"知识库很大但还没有检索服务"的阶段。
    """

    def __init__(self, cfg: dict, limits: dict, redact: list):
        root = _req(cfg, "root")
        self.root = Path(_resolve_env(root)).expanduser().resolve()
        if not self.root.is_dir():
            raise ConfigError(f"folder.root 不是目录：{self.root}")
        self.exts = {
            str(e).lower() if str(e).startswith(".") else f".{e}".lower()
            for e in (cfg.get("extensions") or [".md", ".txt"])
        }
        self.limits = limits
        self.redact = redact

    def _files(self):
        for path in sorted(self.root.rglob("*")):
            if path.is_file() and path.suffix.lower() in self.exts:
                yield path

    def _rel(self, path: Path) -> str:
        return str(path.relative_to(self.root))

    @staticmethod
    def _score(body: str, title: str, terms: list[str]) -> float:
        """标题命中占主导，正文词频做饱和。

        直接把正文出现次数相加会奖励关键词堆砌：一篇提了二十次"报销"的杂记会压过标题就叫
        《报销管理办法》的那一篇。所以正文用 tf/(tf+k) 形式饱和（BM25 的那个思路），
        每个词的贡献封顶，命中与否比命中多少更重要。
        """
        total = 0.0
        for term in terms:
            body_tf = body.count(term)
            if body_tf:
                total += 10.0 * body_tf / (body_tf + 3.0)  # 渐近于 10，堆砌无收益
            if term in title:
                total += 30.0  # 文件名往往就是主题词
        return total

    def search(self, query: str, limit: int) -> dict:
        terms = [t for t in re.split(r"\s+", (query or "").strip().lower()) if t]
        if not terms:
            return {"error": "查询词不能为空"}
        scored = []
        for path in self._files():
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            low, title = text.lower(), self._rel(path).lower()
            score = self._score(low, title, terms)
            if score:
                scored.append((score, path, text, terms))
        scored.sort(key=lambda x: (-x[0], str(x[1])))
        results = []
        for score, path, text, _ in scored[:limit]:
            results.append(
                {
                    "id": self._rel(path),
                    "title": path.stem,
                    "score": score,
                    "snippet": _clip(
                        _scrub(_around(text, terms), self.redact), self.limits["snippet_chars"]
                    ),
                }
            )
        return {"ok": True, "count": len(results), "results": results}

    def get(self, doc_id: str) -> dict:
        # 目录穿越守卫：doc_id 来自模型，`../../etc/passwd` 必须落在 root 之外时被拒。
        try:
            target = (self.root / str(doc_id)).resolve()
            target.relative_to(self.root)
        except (ValueError, OSError):
            return {"error": f"文档 id 越界：{doc_id}"}
        if not target.is_file() or target.suffix.lower() not in self.exts:
            return {"error": f"找不到文档：{doc_id}"}
        try:
            text = target.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            return {"error": f"读取失败：{exc}"}
        return {
            "ok": True,
            "id": self._rel(target),
            "content": _clip(_scrub(text, self.redact), self.limits["doc_chars"]),
        }


def _req(cfg: dict, key: str) -> str:
    value = cfg.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"缺少必填配置项 {key}")
    return value.strip()


def _clip(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n…（超过 {limit} 字符，已截断）"


def _scrub(text: str, patterns: list) -> str:
    for pattern in patterns:
        text = pattern.sub("«已脱敏»", text)
    return text


def _around(text: str, terms: list[str], window: int = 200) -> str:
    """取第一个命中词周围的片段——比返回开头两百字有用得多。"""
    low = text.lower()
    for term in terms:
        idx = low.find(term)
        if idx >= 0:
            start = max(0, idx - window // 2)
            return ("…" if start else "") + text[start : start + window].strip() + "…"
    return text[:window].strip()


def build_backend(cfg: dict) -> Backend:
    if not isinstance(cfg, dict):
        raise ConfigError("配置顶层必须是对象")
    limits = dict(DEFAULT_LIMITS)
    for key, value in (cfg.get("limits") or {}).items():
        if key in limits:
            try:
                limits[key] = type(limits[key])(value)
            except (TypeError, ValueError) as exc:
                raise ConfigError(f"limits.{key} 不是数字：{value!r}") from exc
    redact = []
    for pattern in cfg.get("redact") or []:
        try:
            redact.append(re.compile(pattern))
        except re.error as exc:
            raise ConfigError(f"redact 正则 {pattern!r} 无效：{exc}") from exc

    kind = (cfg.get("backend") or "").strip().lower()
    if kind == "http":
        return HttpBackend(cfg.get("http") or {}, limits, redact)
    if kind == "folder":
        return FolderBackend(cfg.get("folder") or {}, limits, redact)
    raise ConfigError('backend 必须是 "http" 或 "folder"')


SEARCH_SCHEMA = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "检索词。用主题词，不要整句提问。"},
        "limit": {"type": "integer", "description": "最多返回几条（默认按服务端配置）"},
    },
    "required": ["query"],
    "additionalProperties": False,
}

GET_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string", "description": "kb_search 结果里的 id"},
    },
    "required": ["id"],
    "additionalProperties": False,
}


class Server:
    def __init__(self, backend: Backend, limits: dict):
        self.backend = backend
        self.limits = limits

    def call(self, name: str, args: dict) -> dict:
        args = args or {}
        if name == "kb_search":
            query = args.get("query")
            if not isinstance(query, str) or not query.strip():
                return {"error": "query 必须是非空字符串"}
            limit = args.get("limit") or self.limits["max_results"]
            try:
                limit = max(1, min(int(limit), self.limits["max_results"]))
            except (TypeError, ValueError):
                limit = self.limits["max_results"]
            return self.backend.search(query.strip(), limit)
        if name == "kb_get":
            doc_id = args.get("id")
            if not isinstance(doc_id, str) or not doc_id.strip():
                return {"error": "id 必须是非空字符串"}
            return self.backend.get(doc_id.strip())
        return {"error": f"未知工具：{name}"}


async def serve(server: Server, name: str) -> None:
    try:
        from mcp.server import Server as MCPServer
        from mcp.server.stdio import stdio_server
        from mcp.types import TextContent, Tool as MCPTool
    except ImportError:  # pragma: no cover
        sys.stderr.write("需要 mcp 包：pip install 'mcp>=1.1,<2'\n")
        raise SystemExit(2)

    app = MCPServer(name)

    @app.list_tools()
    async def list_tools() -> list:
        return [
            MCPTool(
                name="kb_search",
                description=(
                    "在企业知识库里检索。返回标题、片段与文档 id；要全文再调 kb_get。"
                    "权限由知识库按调用者校验——搜不到不等于不存在，可能是无权查看。"
                ),
                inputSchema=SEARCH_SCHEMA,
            ),
            MCPTool(
                name="kb_get",
                description="按 kb_search 返回的 id 取文档全文。",
                inputSchema=GET_SCHEMA,
            ),
        ]

    @app.call_tool()
    async def call_tool(tool_name: str, arguments: dict) -> list:
        result = server.call(tool_name, arguments or {})
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    async with stdio_server() as (read, write):
        await app.run(read, write, app.create_initialization_options())


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="企业知识库检索 MCP server")
    ap.add_argument("--config", required=True, help="kb.json 路径")
    ap.add_argument("--name", default="corp-kb")
    ap.add_argument("--check", action="store_true", help="只校验配置，不启动服务")
    ap.add_argument("--query", default="", help="配合 --check 试搜一次")
    args = ap.parse_args(argv)

    try:
        raw = json.loads(Path(args.config).expanduser().read_text(encoding="utf-8"))
        backend = build_backend(raw)
    except FileNotFoundError:
        sys.stderr.write(f"[配置错误] 找不到 {args.config}\n")
        return 2
    except json.JSONDecodeError as exc:
        sys.stderr.write(f"[配置错误] 不是合法 JSON：{exc}\n")
        return 2
    except ConfigError as exc:
        sys.stderr.write(f"[配置错误] {exc}\n")
        return 2

    limits = dict(DEFAULT_LIMITS)
    limits.update({k: v for k, v in (raw.get("limits") or {}).items() if k in limits})
    server = Server(backend, limits)

    if args.check:
        print(f"配置合法，后端：{raw.get('backend')}")
        if args.query:
            print(json.dumps(server.call("kb_search", {"query": args.query}), ensure_ascii=False, indent=2))
        return 0

    import asyncio

    asyncio.run(serve(server, args.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
