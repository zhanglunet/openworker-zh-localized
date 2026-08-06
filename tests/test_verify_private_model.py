"""私有模型验证脚本的判定逻辑。

这个脚本的输出会被直接抄进模型能力声明，所以它判错的代价不是"报告难看"，
而是**一条看起来有依据的错误事实**被写进配置，之后没人会回头复查。

实测中真的踩到的两个：

1. 基础对话探针用 max_tokens=32 且只读 message.content。推理模型把预算全烧在
   reasoning_content 上，content 回来是空的 —— 于是好好的模型被判"基础对话不通"，
   而且该判定会 return 掉后面全部探测，人再去查端点和凭据，查半天什么都没有。
2. 并行工具调用探针把 60 秒超时 except 成 False。超时是"没测出来"，不是"不支持"；
   写成 false 会让 Agent 永远串行执行，慢一倍，且没有任何地方提示重测。
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "docs" / "enterprise" / "templates" / "verify-private-model.py"
)


def _load():
    spec = importlib.util.spec_from_file_location("verify_private_model", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vpm = _load()


class FakeProbe:
    """按脚本调用顺序回放预设响应。model/base 只是占位。"""

    model = "corp/model"

    def __init__(self, chat_responses, stream_chunks=3, models=("corp/model",)):
        self._chat = list(chat_responses)
        self._stream = stream_chunks
        self._models = list(models)
        self.calls = []

    def models(self):
        return self._models

    def chat(self, messages, **kw):
        self.calls.append(kw)
        item = self._chat.pop(0) if self._chat else {}
        if isinstance(item, Exception):
            raise item
        return item

    def chat_stream(self, messages):
        return ["chunk"] * self._stream


def _msg(**fields):
    return {"choices": [{"message": fields}], "usage": {"prompt_tokens": 5}}


_TOOL_CALL = {"id": "c1", "type": "function", "function": {"name": "get_weather", "arguments": "{}"}}


# -- 缺陷 1：推理模型的假阴性 -------------------------------------------------------
def test_reasoning_model_with_empty_content_is_not_a_failure():
    """content 为空但有 reasoning_content —— 链路是通的，不能判失败。

    把 chat 探针改回「只看 content」，这条必须变红。
    """
    probe = FakeProbe([_msg(content="", reasoning_content="嗯，用户要两个字……")])
    out = vpm.run(probe)
    ok, note = out["chat"]
    assert ok is True, note
    assert "推理" in note


@pytest.mark.parametrize("field", ["reasoning_content", "reasoning", "thinking"])
def test_all_known_reasoning_field_names_are_recognized(field):
    """各家字段名不统一，认少了就还是假阴性。"""
    probe = FakeProbe([_msg(content=None, **{field: "思考中"})])
    assert vpm.run(probe)["chat"][0] is True


def test_basic_chat_probe_asks_for_enough_tokens():
    """max_tokens 太小，推理模型永远吐不出 content。32 是原来的值，被这条钉死。"""
    probe = FakeProbe([_msg(content="可以")])
    vpm.run(probe)
    assert probe.calls[0].get("max_tokens", 0) >= 256


def test_truly_empty_response_is_still_a_failure():
    """修假阴性不能修成"什么都算通过"。"""
    probe = FakeProbe([_msg(content="", reasoning_content="")])
    ok, note = vpm.run(probe)["chat"]
    assert ok is False and "都为空" in note


def test_failed_chat_short_circuits_the_rest():
    probe = FakeProbe([RuntimeError("connection refused")])
    out = vpm.run(probe)
    assert out["chat"][0] is False
    assert "streaming" not in out, "基础对话不通时不该继续探测"


# -- 缺陷 2：超时被记成「不支持」---------------------------------------------------
def test_parallel_timeout_is_undetermined_not_false():
    """超时 → None（未判定），不是 False。

    改回 `out["parallel_tool_calls"] = (False, _err(exc))` 这条必须变红。
    """
    probe = FakeProbe([
        _msg(content="可以"),                 # chat
        _msg(content=None, tool_calls=[_TOOL_CALL]),  # tools
        TimeoutError("The read operation timed out"),  # parallel
        _msg(content="ok"),                   # tool_result_roundtrip
        _msg(content="ok"),                   # vision
    ])
    out = vpm.run(probe)
    assert out["parallel_tool_calls"][0] is None
    assert "超时" in out["parallel_tool_calls"][1]


def test_parallel_explicit_refusal_is_still_false():
    """明确的 4xx 拒绝仍然是 False —— 不能因为怕误判就全都判成未知。"""
    probe = FakeProbe([
        _msg(content="可以"),
        _msg(content=None, tool_calls=[_TOOL_CALL]),
        ValueError("HTTP 400 Bad Request: parallel tool calls not supported"),
        _msg(content="ok"),
        _msg(content="ok"),
    ])
    assert vpm.run(probe)["parallel_tool_calls"][0] is False


def test_single_tool_call_is_false_not_undetermined():
    """一轮只回一个调用 = 实测出来的不支持，跟超时是两回事。"""
    probe = FakeProbe([
        _msg(content="可以"),
        _msg(content=None, tool_calls=[_TOOL_CALL]),
        _msg(content=None, tool_calls=[_TOOL_CALL]),
        _msg(content="ok"),
        _msg(content="ok"),
    ])
    ok, note = vpm.run(probe)["parallel_tool_calls"]
    assert ok is False and "只肯一个一个来" in note


@pytest.mark.parametrize(
    "exc",
    [
        TimeoutError("timed out"),
        OSError("The read operation timed out"),
    ],
)
def test_timeout_detection_covers_the_shapes_urllib_raises(exc):
    assert vpm._is_timeout(exc) is True


def test_non_timeout_is_not_mistaken_for_one():
    assert vpm._is_timeout(ValueError("HTTP 400 Bad Request")) is False


# -- 声明生成：未判定的能力不能落成 false ------------------------------------------
def test_undetermined_capability_is_omitted_from_the_declaration():
    """宁可缺一个字段落到保守默认，也不能把「没测出来」写成「不支持」——
    后者是一条看起来有依据的错误事实，之后没人会回头复查。"""
    results = {
        "tools": (True, ""),
        "streaming": (True, ""),
        "parallel_tool_calls": (None, "超时"),
        "vision": (True, ""),
    }
    entry = vpm.declaration("custom:m", "M", results, None)["models"]["custom:m"]
    assert "parallel_tool_calls" not in entry
    assert entry["tools"] is True and entry["vision"] is True


def test_determined_capabilities_are_written():
    for value in (True, False):
        results = {
            "tools": (True, ""),
            "streaming": (True, ""),
            "parallel_tool_calls": (value, ""),
            "vision": (False, ""),
        }
        entry = vpm.declaration("custom:m", "M", results, None)["models"]["custom:m"]
        assert entry["parallel_tool_calls"] is value


def test_context_window_only_written_when_given():
    base = {"tools": (True, ""), "streaming": (True, ""), "parallel_tool_calls": (True, ""), "vision": (True, "")}
    assert "context_window" not in vpm.declaration("custom:m", "M", base, None)["models"]["custom:m"]
    assert vpm.declaration("custom:m", "M", base, 200_000)["models"]["custom:m"]["context_window"] == 200_000


# -- 报告渲染 ---------------------------------------------------------------------
def test_report_renders_undetermined_distinctly(capsys):
    results = {
        "chat": (True, "1.0s"),
        "streaming": (True, ""),
        "tools": (True, ""),
        "parallel_tool_calls": (None, "超时，未能判定"),
        "tool_result_roundtrip": (True, ""),
        "vision": (True, ""),
    }
    vpm.report("custom:m", results)
    out = capsys.readouterr().out
    assert "⚠️" in out, "未判定必须和 ❌ 区分开，否则人会当成不支持"
    assert "未判定" in out
    assert "不要默认填 false" in out


def test_report_blocks_on_real_failures(capsys):
    results = {"chat": (True, ""), "tools": (False, ""), "tool_result_roundtrip": (False, "")}
    assert vpm.report("custom:m", results) is False
    assert "只能当聊天模型" in capsys.readouterr().out


def test_report_flags_half_a_toolchain(capsys):
    """能发起调用却不接受回执 = 多轮任务会断，这个必须拦。"""
    results = {"chat": (True, ""), "tools": (True, ""), "tool_result_roundtrip": (False, "")}
    assert vpm.report("custom:m", results) is False
    assert "半截" in capsys.readouterr().out
