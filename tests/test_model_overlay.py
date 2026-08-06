"""Locally declared models (`<state-dir>/models.json`).

The curated matrix can't contain a privately deployed model — nobody outside that
deployment knows it exists — so without a declaration such a model runs on
`capabilities.py`'s conservative fallbacks: tool calls serialised, context meter hidden.
These tests pin the escape hatch: a declaration reaches every consumer of the matrix
(capabilities probe, GUI labels, context meter, per-provider suggestions), and a broken
declaration degrades to "ignored" rather than to a crash on startup.
"""

from __future__ import annotations

import json

import pytest

from coworker.providers import matrix, model_overlay
from coworker.providers.capabilities import capabilities_for


@pytest.fixture
def overlay(tmp_path, monkeypatch):
    """Point the overlay at a temp file and keep its mtime cache honest between tests."""
    path = tmp_path / "models.json"
    monkeypatch.setattr(model_overlay, "overlay_path", lambda: path)
    monkeypatch.delenv("COWORKER_DISABLE_MODEL_OVERLAY", raising=False)

    def write(payload) -> None:
        path.write_text(
            payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False),
            encoding="utf-8",
        )
        model_overlay.invalidate()

    model_overlay.invalidate()
    yield write
    model_overlay.invalidate()


CORP = "custom:qwen3-72b-corp"


def test_no_file_changes_nothing(overlay):
    assert model_overlay.declared() == {}
    assert matrix.entry_for(CORP) is None
    # The built-in matrix is still whole.
    assert matrix.entry_for("gpt-5.6-sol") is not None


def test_declaration_reaches_the_capability_probe(overlay):
    overlay({"models": {CORP: {"label": "Qwen3 72B · 内网", "parallel_tool_calls": True,
                               "context_window": 131072}}})
    caps = capabilities_for(CORP)
    assert caps.tools is True
    assert caps.parallel_tool_calls is True, (
        "without the overlay this model would fall to the conservative heuristics and "
        "run its tool calls one at a time"
    )
    assert matrix.model_labels()[CORP] == "Qwen3 72B · 内网"
    assert matrix.model_context_windows()[CORP] == 131072
    assert "qwen3-72b-corp" in matrix.models_for_provider("custom")


def test_declaration_overrides_a_curated_entry(overlay):
    """A gateway may serve a familiar id with different limits — the local truth wins."""
    before = matrix.entry_for("gpt-5.6-sol")
    assert before is not None and before.context_window != 8192
    overlay({"models": {"gpt-5.6-sol": {"label": "网关代理版", "context_window": 8192}}})
    after = matrix.entry_for("gpt-5.6-sol")
    assert after.label == "网关代理版" and after.context_window == 8192


def test_defaults_are_conservative_but_usable(overlay):
    """An under-specified entry should behave like the heuristics, not invent capabilities."""
    overlay({"models": {CORP: {}}})
    caps = capabilities_for(CORP)
    assert caps.tools is True and caps.streaming is True  # or it isn't an agent model
    assert caps.vision is False and caps.parallel_tool_calls is False
    assert matrix.entry_for(CORP).label == CORP  # id doubles as its own display name


def test_bare_id_declares_for_the_default_route(overlay, caplog):
    """Bare ids are legal — the matrix stores OpenAI's rows that way, and an endpoint added
    as the `openai` provider with a custom base_url serves bare names too. Refusing them
    would block a real setup. It is still the likeliest typo, so it must be logged."""
    with caplog.at_level("INFO", logger="coworker.providers"):
        overlay({"models": {"qwen3-72b-corp": {"label": "x"}}})
        entry = matrix.entry_for("qwen3-72b-corp")
    assert entry is not None and entry.label == "x"
    assert "custom:qwen3-72b-corp" in caplog.text, "the routing consequence must be spelled out"


@pytest.mark.parametrize(
    "payload",
    [
        "{ this is not json",
        json.dumps([1, 2, 3]),
        json.dumps({"models": "nope"}),
        json.dumps({"nothing": {}}),
    ],
)
def test_malformed_file_is_ignored_not_fatal(overlay, payload):
    overlay(payload)
    assert model_overlay.declared() == {}
    assert matrix.entry_for("gpt-5.6-sol") is not None  # built-ins still resolve


def test_bad_field_types_fall_back_per_field(overlay):
    overlay({"models": {CORP: {"label": 5, "vision": "yes", "context_window": "big"}}})
    entry = matrix.entry_for(CORP)
    assert entry is not None
    assert entry.label == CORP  # non-string label ignored
    assert entry.caps.vision is False  # non-bool flag ignored
    assert entry.context_window is None  # non-numeric window ignored


def test_non_positive_window_ignored(overlay):
    overlay({"models": {CORP: {"context_window": 0}}})
    assert matrix.entry_for(CORP).context_window is None


def test_hot_reload_on_change(overlay):
    overlay({"models": {CORP: {"context_window": 1000}}})
    assert matrix.entry_for(CORP).context_window == 1000
    overlay({"models": {CORP: {"context_window": 2000}}})
    assert matrix.entry_for(CORP).context_window == 2000


def test_kill_switch(overlay, monkeypatch):
    overlay({"models": {CORP: {"label": "x"}}})
    assert matrix.entry_for(CORP) is not None
    monkeypatch.setenv("COWORKER_DISABLE_MODEL_OVERLAY", "1")
    assert matrix.entry_for(CORP) is None
