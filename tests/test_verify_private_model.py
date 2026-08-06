"""The private-model probe script, driven against a stub OpenAI-compatible endpoint.

"OpenAI-compatible" is a spectrum in practice: gateways that accept `tools` and never
return `tool_calls`, that only ever emit one call per turn, that reject `role=tool`
messages, that 404 on `/models`. None of those raise an error — they just make the agent
quietly worse. The script exists to name them before a rollout, so these tests drive it
against endpoints that fail in exactly those ways.
"""

from __future__ import annotations

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest

SCRIPT = (
    Path(__file__).resolve().parent.parent
    / "docs"
    / "enterprise"
    / "templates"
    / "verify-private-model.py"
)


def _load_script():
    spec = importlib.util.spec_from_file_location("verify_private_model", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


vpm = _load_script()


class _Stub:
    """A configurable fake endpoint. `behaviour` picks which compatibility gaps to fake."""

    def __init__(self, behaviour: str = "full"):
        self.behaviour = behaviour
        self.seen: list[dict] = []
        handler = self._handler()
        self.httpd = HTTPServer(("127.0.0.1", 0), handler)
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    @property
    def base_url(self) -> str:
        host, port = self.httpd.server_address
        return f"http://{host}:{port}/v1"

    def stop(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()

    def _handler(self):
        outer = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *a):  # keep pytest output clean
                pass

            def _send(self, code: int, payload, raw: bool = False):
                body = payload if raw else json.dumps(payload).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path.endswith("/models"):
                    if outer.behaviour == "no_models_endpoint":
                        return self._send(404, {"error": "not found"})
                    return self._send(200, {"data": [{"id": "corp-model"}]})
                self._send(404, {"error": "nope"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0))
                req = json.loads(self.rfile.read(length) or b"{}")
                outer.seen.append(req)

                has_tool_msg = any(m.get("role") == "tool" for m in req.get("messages", []))
                if has_tool_msg and outer.behaviour == "no_tool_results":
                    return self._send(400, {"error": "role 'tool' is not supported"})

                if req.get("stream"):
                    if outer.behaviour == "no_streaming":
                        return self._send(400, {"error": "stream unsupported"})
                    chunk = json.dumps({"choices": [{"delta": {"content": "1"}}]})
                    body = f"data: {chunk}\n\ndata: [DONE]\n\n".encode()
                    return self._send(200, body, raw=True)

                # Vision probe: content is a list of parts.
                content = (req.get("messages") or [{}])[-1].get("content")
                if isinstance(content, list):
                    if outer.behaviour in ("no_vision", "text_only"):
                        return self._send(400, {"error": "image input unsupported"})
                    return self._send(200, self._msg({"content": "white"}))

                if req.get("tools") and not has_tool_msg:
                    if outer.behaviour in ("tools_accepted_never_called", "text_only"):
                        return self._send(200, self._msg({"content": "I cannot call tools"}))
                    wants_two = "同时" in json.dumps(req.get("messages"), ensure_ascii=False)
                    calls = [self._call("get_weather", "call_1")]
                    if wants_two and outer.behaviour != "serial_tools_only":
                        calls.append(self._call("get_time", "call_2"))
                    return self._send(200, self._msg({"content": None, "tool_calls": calls}))

                return self._send(200, self._msg({"content": "可以"}))

            @staticmethod
            def _call(name: str, cid: str) -> dict:
                return {
                    "id": cid,
                    "type": "function",
                    "function": {"name": name, "arguments": '{"city":"x"}'},
                }

            @staticmethod
            def _msg(message: dict) -> dict:
                return {
                    "choices": [{"message": {"role": "assistant", **message}}],
                    "usage": {"prompt_tokens": 10, "completion_tokens": 2},
                }

        return Handler


@pytest.fixture
def stub():
    made: list[_Stub] = []

    def build(behaviour: str = "full") -> _Stub:
        s = _Stub(behaviour)
        made.append(s)
        return s

    yield build
    for s in made:
        s.stop()


def _run(server: _Stub):
    probe = vpm.Probe(server.base_url, "corp-model", "k")
    return vpm.run(probe)


def _ok(results, key) -> bool:
    return bool(results.get(key, (False, ""))[0])


def test_fully_capable_endpoint_passes(stub):
    results = _run(stub("full"))
    for key in ("models_endpoint", "chat", "streaming", "tools",
                "parallel_tool_calls", "tool_result_roundtrip", "vision"):
        assert _ok(results, key), (key, results.get(key))
    assert vpm.report("custom:corp-model", results) is True


def test_tools_accepted_but_never_called_is_blocking(stub):
    """The nastiest failure mode: nothing errors, the model just never calls a tool."""
    results = _run(stub("tools_accepted_never_called"))
    assert _ok(results, "chat") and not _ok(results, "tools")
    assert vpm.report("custom:corp-model", results) is False


def test_tool_results_rejected_is_blocking(stub):
    """Can start a tool call but won't accept the result — a half tool loop, worse than none."""
    results = _run(stub("no_tool_results"))
    assert _ok(results, "tools")
    assert not _ok(results, "tool_result_roundtrip")
    assert vpm.report("custom:corp-model", results) is False


def test_serial_only_tools_is_usable_but_declared_false(stub):
    results = _run(stub("serial_tools_only"))
    assert _ok(results, "tools") and not _ok(results, "parallel_tool_calls")
    assert vpm.report("custom:corp-model", results) is True  # usable, just slower
    decl = vpm.declaration("custom:corp-model", "", results, None)
    assert decl["models"]["custom:corp-model"]["parallel_tool_calls"] is False


def test_missing_streaming_and_models_endpoint_are_not_blocking(stub):
    for behaviour, key in (("no_streaming", "streaming"), ("no_models_endpoint", "models_endpoint")):
        results = _run(stub(behaviour))
        assert not _ok(results, key)
        assert vpm.report("custom:corp-model", results) is True


def test_declaration_matches_probe_results(stub):
    results = _run(stub("no_vision"))
    decl = vpm.declaration("custom:corp-model", "内网 Qwen", results, 131072)
    entry = decl["models"]["custom:corp-model"]
    assert entry["label"] == "内网 Qwen"
    assert entry["context_window"] == 131072
    assert entry["vision"] is False
    assert entry["tools"] is True
    # OpenAI-compatible chat APIs have no inline file part; PDFs go through pdf_support.py.
    assert entry["pdf"] is False


def test_declaration_is_consumable_by_the_overlay(stub, tmp_path, monkeypatch):
    """End to end: what the probe emits must be exactly what the runtime reads back."""
    from coworker.providers import matrix, model_overlay

    results = _run(stub("full"))
    decl = vpm.declaration("custom:corp-model", "内网模型", results, 65536)
    path = tmp_path / "models.json"
    path.write_text(json.dumps(decl, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(model_overlay, "overlay_path", lambda: path)
    model_overlay.invalidate()
    try:
        entry = matrix.entry_for("custom:corp-model")
        assert entry is not None
        assert entry.label == "内网模型"
        assert entry.context_window == 65536
        assert entry.caps.parallel_tool_calls is True
    finally:
        model_overlay.invalidate()


def test_dead_endpoint_reports_cleanly():
    probe = vpm.Probe("http://127.0.0.1:9", "corp-model", "")  # discard port
    results = vpm.run(probe)
    assert not _ok(results, "chat")
    assert vpm.report("custom:corp-model", results) is False
