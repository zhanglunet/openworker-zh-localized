#!/usr/bin/env python3
"""私有模型接入验证 —— 对着企业自建的 OpenAI 兼容端点跑一遍能力矩阵。

为什么需要它：OpenWorker 把模型能力当既定事实用（能不能并行工具调用、上下文多大、
支不支持流式），而私有部署的模型不在内置矩阵里，会落到保守启发式——并行工具调用关掉、
上下文水位条不显示。想让它跑在真实能力上，就得先知道真实能力是什么。

「兼容 OpenAI 接口」在实践中是个光谱：有的网关不支持 stream、有的 tools 字段收下了却从不
返回 tool_calls、有的一次只肯回一个 tool_call。这些差别不会报错，只会让 Agent 悄悄变笨。
本脚本逐项实测并给出结论，最后直接生成 <state-dir>/models.json 该写的内容。

用法：
    python3 verify-private-model.py \
        --base-url https://llm.corp.example/v1 \
        --model qwen3-72b-corp \
        --api-key "$CORP_LLM_KEY"          # 也可用环境变量 OPENWORKER_PROBE_KEY

    # 只看结论不写文件；加 --emit 打印可直接粘贴的 models.json 片段
    python3 verify-private-model.py ... --emit
    # 直接写入（默认写 <state-dir>/models.json，已存在的同名条目会被覆盖）
    python3 verify-private-model.py ... --write

只依赖标准库（urllib），不需要装 openai SDK —— 内网机器上少一个依赖少一分麻烦。
"""

from __future__ import annotations

import argparse
import json
import os
import ssl
import sys
import time
import urllib.error
import urllib.request
from typing import Any, Optional

TIMEOUT = 60

# 探针用的工具定义：两个互不相关的函数，用来看端点会不会在一轮里同时要两个。
_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": "Get the current time in a city.",
            "parameters": {
                "type": "object",
                "properties": {"city": {"type": "string"}},
                "required": ["city"],
            },
        },
    },
]


class Probe:
    def __init__(self, base_url: str, model: str, api_key: str, insecure: bool = False):
        self.base = base_url.rstrip("/")
        self.model = model
        self.key = api_key
        self.ctx = None
        if insecure:
            # 内网自签证书很常见。默认仍然校验，要跳过必须显式 --insecure。
            self.ctx = ssl.create_default_context()
            self.ctx.check_hostname = False
            self.ctx.verify_mode = ssl.CERT_NONE

    def _request(self, path: str, payload: Optional[dict] = None, stream: bool = False):
        url = f"{self.base}{path}"
        headers = {"Content-Type": "application/json"}
        if self.key:
            headers["Authorization"] = f"Bearer {self.key}"
        data = json.dumps(payload).encode() if payload is not None else None
        req = urllib.request.Request(url, data=data, headers=headers, method="POST" if data else "GET")
        return urllib.request.urlopen(req, timeout=TIMEOUT, context=self.ctx)

    def chat(self, messages: list, **extra) -> dict:
        payload = {"model": self.model, "messages": messages, **extra}
        with self._request("/chat/completions", payload) as resp:
            return json.loads(resp.read().decode())

    def chat_stream(self, messages: list) -> list[str]:
        payload = {"model": self.model, "messages": messages, "stream": True}
        chunks = []
        with self._request("/chat/completions", payload, stream=True) as resp:
            for raw in resp:
                line = raw.decode("utf-8", "replace").strip()
                if not line.startswith("data:"):
                    continue
                body = line[5:].strip()
                if body == "[DONE]":
                    break
                chunks.append(body)
        return chunks

    def models(self) -> list[str]:
        with self._request("/models") as resp:
            data = json.loads(resp.read().decode())
        rows = data.get("data") if isinstance(data, dict) else None
        return [r.get("id", "") for r in rows or [] if isinstance(r, dict)]


def _err(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        try:
            body = exc.read().decode("utf-8", "replace")[:300]
        except Exception:
            body = ""
        return f"HTTP {exc.code} {exc.reason} {body}".strip()
    return f"{type(exc).__name__}: {exc}"


def _is_timeout(exc: Exception) -> bool:
    """区分「超时」与「明确拒绝」。socket.timeout 在 py3.10+ 是 TimeoutError 的别名，
    但 urllib 有时把它裹进 URLError，所以文本兜底一层。"""
    if isinstance(exc, TimeoutError):
        return True
    reason = getattr(exc, "reason", None)
    if isinstance(reason, TimeoutError):
        return True
    return "timed out" in str(exc).lower()


def run(probe: Probe) -> dict[str, Any]:
    """逐项实测。每项返回 (通过?, 说明)，任何一项失败都不中断后面的探测。"""
    out: dict[str, Any] = {}

    # 0) /models —— 端点是否真的在线、模型名对不对
    try:
        ids = probe.models()
        listed = probe.model in ids
        out["models_endpoint"] = (
            True,
            f"可用，返回 {len(ids)} 个模型" + ("，包含目标模型" if listed else "，但**不含**目标模型"),
        )
        out["_model_listed"] = listed
    except Exception as exc:
        out["models_endpoint"] = (False, f"不可用（{_err(exc)}）—— GUI 的「获取模型」按钮会失败")

    # 1) 普通对话 —— 最低门槛
    #
    # max_tokens 给足 256，不是 32：推理模型（deepseek-v4-pro 这类）会先烧一段
    # reasoning_content 再吐 content，32 个 token 全被推理吃掉，content 回来是空的，
    # 于是"模型好好的"被判成"基础对话不通"。这个假阴性会一路传染——报告说不通，
    # 后面的探测全部 return 掉，人再去查端点和凭据，查半天什么都没有。
    try:
        t0 = time.time()
        res = probe.chat([{"role": "user", "content": "只回复两个字：可以"}], max_tokens=256)
        msg = (res.get("choices") or [{}])[0].get("message", {}) or {}
        text = msg.get("content") or ""
        # 各家推理模型的字段名不统一，见到哪个算哪个
        reasoning = ""
        for k in ("reasoning_content", "reasoning", "thinking"):
            if msg.get(k):
                reasoning = str(msg[k])
                break
        usage = res.get("usage") or {}
        took = time.time() - t0
        if text.strip():
            out["chat"] = (True, f"{took:.1f}s，回复 {len(text)} 字符")
        elif reasoning.strip():
            # 能推理说明链路是通的，只是 content 为空 —— 不当失败，但要说清楚
            out["chat"] = (
                True,
                f"{took:.1f}s，content 为空但返回了 {len(reasoning)} 字符推理内容"
                "（推理模型；如仍为空请调大 max_tokens 复测）",
            )
        else:
            out["chat"] = (False, f"{took:.1f}s，content 与推理内容都为空")
        out["_usage"] = bool(usage.get("prompt_tokens"))
    except Exception as exc:
        out["chat"] = (False, _err(exc))
        return out  # 连基本对话都不通，后面没必要测

    # 2) 流式 —— 关掉会让界面从逐字变成整段蹦出来
    try:
        chunks = probe.chat_stream([{"role": "user", "content": "数到三"}])
        out["streaming"] = (len(chunks) > 0, f"收到 {len(chunks)} 个数据块")
    except Exception as exc:
        out["streaming"] = (False, _err(exc))

    # 3) 工具调用 —— Agent 的命脉，不支持就只能当聊天模型
    tool_calls = []
    try:
        res = probe.chat(
            [{"role": "user", "content": "北京现在天气怎么样？用工具查。"}],
            tools=_TOOLS,
            tool_choice="auto",
        )
        msg = (res.get("choices") or [{}])[0].get("message", {}) or {}
        tool_calls = msg.get("tool_calls") or []
        out["tools"] = (
            bool(tool_calls),
            f"返回 {len(tool_calls)} 个 tool_call" if tool_calls else "**收下了 tools 但没有返回 tool_calls**",
        )
    except Exception as exc:
        out["tools"] = (False, _err(exc))

    # 4) 并行工具调用 —— 内置矩阵里最常被高估的一项
    if tool_calls:
        try:
            res = probe.chat(
                [{"role": "user", "content": "同时查北京的天气和东京的时间，两个都要。"}],
                tools=_TOOLS,
                tool_choice="auto",
            )
            calls = ((res.get("choices") or [{}])[0].get("message", {}) or {}).get("tool_calls") or []
            out["parallel_tool_calls"] = (
                len(calls) >= 2,
                f"一轮返回 {len(calls)} 个调用" + ("" if len(calls) >= 2 else "（只肯一个一个来）"),
            )
        except Exception as exc:
            # 超时 ≠ 不支持。把网关抖动记成 parallel_tool_calls=false 会被写进配置，
            # 之后 Agent 永远串行执行，慢一倍，而且没有任何地方会提示你重测。
            # 所以超时单独记成 None（未判定），由调用方决定重试或留空。
            out["parallel_tool_calls"] = (
                None if _is_timeout(exc) else False,
                _err(exc) + ("　←　超时，未能判定，请重测" if _is_timeout(exc) else ""),
            )
    else:
        out["parallel_tool_calls"] = (False, "跳过：工具调用本身就不通")

    # 5) 工具结果回传 —— 有的端点能发起调用却不接受 role=tool 的回执，等于半截工具链
    if tool_calls:
        try:
            first = tool_calls[0]
            probe.chat(
                [
                    {"role": "user", "content": "北京现在天气怎么样？用工具查。"},
                    {"role": "assistant", "content": None, "tool_calls": tool_calls},
                    {
                        "role": "tool",
                        "tool_call_id": first.get("id", "call_1"),
                        "content": '{"temp_c": 26, "sky": "晴"}',
                    },
                ],
                tools=_TOOLS,
                max_tokens=64,
            )
            out["tool_result_roundtrip"] = (True, "接受 role=tool 回执")
        except Exception as exc:
            out["tool_result_roundtrip"] = (False, f"**不接受工具结果回执**（{_err(exc)}）")
    else:
        out["tool_result_roundtrip"] = (False, "跳过：工具调用本身就不通")

    # 6) 视觉 —— 用一张 1x1 的 PNG 试，失败很正常，不影响文本类任务
    png = (
        "data:image/png;base64,"
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
    )
    try:
        probe.chat(
            [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "这是什么颜色？"},
                        {"type": "image_url", "image_url": {"url": png}},
                    ],
                }
            ],
            max_tokens=32,
        )
        out["vision"] = (True, "接受图片输入")
    except Exception as exc:
        out["vision"] = (False, f"不接受图片（{_err(exc)}）")

    return out


def report(model_id: str, results: dict[str, Any]) -> bool:
    labels = {
        "models_endpoint": "模型列表 /models",
        "chat": "基础对话",
        "streaming": "流式输出",
        "tools": "工具调用",
        "parallel_tool_calls": "并行工具调用",
        "tool_result_roundtrip": "工具结果回传",
        "vision": "图片输入",
    }
    print(f"\n{'=' * 62}\n私有模型接入验证：{model_id}\n{'=' * 62}")
    for key, label in labels.items():
        if key not in results:
            continue
        ok, note = results[key]
        mark = "⚠️" if ok is None else ("✅" if ok else "❌")
        print(f"  {mark}  {label:<14} {note}")

    blocking = []
    if not results.get("chat", (False, ""))[0]:
        blocking.append("基础对话不通 —— 端点/模型名/凭据先查这三样")
    if not results.get("tools", (False, ""))[0]:
        blocking.append("工具调用不可用 —— 这个模型只能当聊天模型，做不了 Agent")
    if results.get("tools", (False, ""))[0] and not results.get(
        "tool_result_roundtrip", (False, "")
    )[0]:
        blocking.append("能发起工具调用但不接受结果回执 —— 工具链是半截的，多轮任务会断")

    print()
    if blocking:
        print("结论：❌ 还不能作为企业默认模型")
        for b in blocking:
            print(f"   · {b}")
    else:
        print("结论：✅ 可以作为企业默认模型")
        par = results.get("parallel_tool_calls", (False, ""))[0]
        if par is None:
            print("   · 并行工具调用**未判定**（超时）—— 声明里已省略该字段，请重测后再填，")
            print("     不要默认填 false：那会让 Agent 永远串行，而且没人会想起来复查")
        elif not par:
            print("   · 并行工具调用不支持 —— 已在生成的声明里关掉，Agent 会串行执行，慢但正确")
        if not results.get("streaming", (False, ""))[0]:
            print("   · 不支持流式 —— 界面会整段蹦出而不是逐字，可用但体验打折")
    return not blocking


def declaration(model_id: str, label: str, results: dict[str, Any], window: Optional[int]) -> dict:
    raw = lambda k: results.get(k, (False, ""))[0]  # noqa: E731
    got = lambda k: bool(raw(k))  # noqa: E731
    entry: dict[str, Any] = {
        "label": label or model_id,
        "tools": got("tools"),
        "streaming": got("streaming"),
        "vision": got("vision"),
        "pdf": False,  # OpenAI 兼容端点都没有内联文件入参，PDF 走 pdf_support.py 降级
    }
    # 未判定（超时）的能力**不写进声明**：宁可缺一个字段让它落到保守默认，
    # 也不能把"没测出来"写成"不支持"——后者是一条看起来有依据的错误事实。
    if raw("parallel_tool_calls") is not None:
        entry["parallel_tool_calls"] = got("parallel_tool_calls")
    if window:
        entry["context_window"] = window
    return {"models": {model_id: entry}}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description="对企业自建的 OpenAI 兼容端点跑一遍能力矩阵，并生成 models.json 声明。"
    )
    ap.add_argument("--base-url", required=True, help="如 https://llm.corp.example/v1")
    ap.add_argument("--model", required=True, help="端点上的模型名，如 qwen3-72b-corp")
    ap.add_argument("--api-key", default=os.environ.get("OPENWORKER_PROBE_KEY", ""),
                    help="可留空（内网免鉴权），或用环境变量 OPENWORKER_PROBE_KEY")
    ap.add_argument("--provider", default="custom", choices=["custom", "ollama", "openai"],
                    help="模型在 OpenWorker 里的 provider 前缀（默认 custom）")
    ap.add_argument("--label", default="", help="界面显示名，如 'Qwen3 72B · 内网'")
    ap.add_argument("--context-window", type=int, default=0,
                    help="上下文窗口（token）。探测不出来，按厂商规格填，用于界面水位条")
    ap.add_argument("--insecure", action="store_true", help="跳过 TLS 校验（自签证书内网）")
    ap.add_argument("--emit", action="store_true", help="打印可粘贴的 models.json 片段")
    ap.add_argument("--write", action="store_true", help="直接写入 <state-dir>/models.json")
    args = ap.parse_args(argv)

    model_id = f"{args.model}" if args.provider == "openai" else f"{args.provider}:{args.model}"
    if args.provider == "openai":
        print("提示：openai 前缀下模型 id 不带前缀，配置里也必须这样写，否则路由会走岔。")

    probe = Probe(args.base_url, args.model, args.api_key, args.insecure)
    results = run(probe)
    ok = report(model_id, results)

    decl = declaration(model_id, args.label, results, args.context_window or None)
    if args.emit or args.write:
        blob = json.dumps(decl, ensure_ascii=False, indent=2)
    if args.emit:
        print(f"\n--- models.json（放到 <state-dir>/models.json）---\n{blob}")
    if args.write:
        try:
            sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
            from coworker.secrets import state_dir  # type: ignore

            target = state_dir() / "models.json"
        except Exception:
            target = None
        if target is None:
            print("\n[跳过写入] 找不到 coworker 包，无法定位 <state-dir>。请用 --emit 手工粘贴。")
        else:
            existing = {}
            if target.exists():
                try:
                    existing = json.loads(target.read_text(encoding="utf-8"))
                except Exception:
                    print(f"\n[警告] 现有 {target} 无法解析，将被覆盖。")
                    existing = {}
            merged = existing.get("models") if isinstance(existing.get("models"), dict) else {}
            merged.update(decl["models"])
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                json.dumps({"models": merged}, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            print(f"\n已写入 {target}")

    if not args.context_window:
        print("\n提示：--context-window 没填，界面的上下文水位条会隐藏（不影响功能）。")
    print("下一步：把 config.toml 的 model 设为 " + repr(model_id) + " —— 必须带前缀，裸名会静默路由到 openai。\n")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
