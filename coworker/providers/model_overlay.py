"""User-declared model entries — the escape hatch from a hardcoded capability matrix.

``matrix.py`` is deliberately small and closed: it lists models we vouch for. Anything else
falls through to ``capabilities.py``'s heuristics, which are conservative by design — an
unknown id gets ``parallel_tool_calls=False``, ``vision=False`` and no context window, so
the GUI hides its fill meter and the engine serialises tool calls.

That default is right for a random model string a user typed. It is wrong for a privately
deployed model behind an OpenAI-compatible gateway (``custom:…``, ``ollama:…``), which is
exactly the case where nobody can send us a pull request to add a matrix row: every such
deployment would otherwise need a source patch to stop running degraded.

So: an optional overlay file, read from ``<state-dir>/models.json``.

    {
      "models": {
        "custom:qwen3-72b-corp": {
          "label": "Qwen3 72B · 内网",
          "context_window": 131072,
          "tools": true,
          "parallel_tool_calls": true,
          "streaming": true,
          "vision": false,
          "pdf": false
        }
      }
    }

Declared entries win over the built-in matrix (a gateway may well serve a familiar name with
a different window). Keys are FULL routed ids, the same form the router receives — a bare
name here would be as wrong as a bare name in a config: it routes to the default provider.

The file is optional, hot-reloaded on mtime change, and a malformed one is ignored with a
warning rather than taking the process down: a typo in a capability declaration must never
be the reason a desktop app won't start.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Optional

from .base import ModelCapabilities

logger = logging.getLogger("coworker.providers")

# Capability flags a declaration may set, with the value used when it stays silent. Tools and
# streaming default true because a model reachable through an OpenAI-compatible endpoint that
# can do neither is not usable as an agent model in the first place; the rest default false so
# an under-specified entry degrades the same way the heuristics would.
_FLAGS: dict[str, bool] = {
    "tools": True,
    "streaming": True,
    "vision": False,
    "pdf": False,
    "parallel_tool_calls": False,
}

_cache: dict[str, Any] = {"stamp": None, "entries": {}}


class DeclaredModel:
    """A validated overlay row. Mirrors matrix.ModelEntry's shape (label / caps /
    context_window) so callers can treat both alike without importing this module."""

    __slots__ = ("label", "caps", "context_window")

    def __init__(self, label: str, caps: ModelCapabilities, context_window: Optional[int]):
        self.label = label
        self.caps = caps
        self.context_window = context_window


def overlay_path() -> Path:
    from ..secrets import state_dir

    return state_dir() / "models.json"


def _stamp(path: Path) -> Optional[tuple[float, int]]:
    try:
        st = path.stat()
    except OSError:
        return None
    return (st.st_mtime, st.st_size)


def _coerce_window(raw: Any, model: str) -> Optional[int]:
    if raw is None:
        return None
    try:
        window = int(raw)
    except (TypeError, ValueError):
        logger.warning("models.json: %s has a non-numeric context_window, ignoring it", model)
        return None
    if window <= 0:
        logger.warning("models.json: %s has a non-positive context_window, ignoring it", model)
        return None
    return window


def _parse_entry(model: str, raw: Any) -> Optional[DeclaredModel]:
    if not isinstance(raw, dict):
        logger.warning("models.json: entry for %s is not an object, skipping", model)
        return None
    flags = {}
    for flag, default in _FLAGS.items():
        value = raw.get(flag, default)
        if not isinstance(value, bool):
            logger.warning(
                "models.json: %s.%s should be true/false, using %s", model, flag, default
            )
            value = default
        flags[flag] = value
    label = raw.get("label")
    if not isinstance(label, str) or not label.strip():
        label = model  # a label is a nicety; the id always works as its own display name
    return DeclaredModel(
        label=label.strip(),
        caps=ModelCapabilities(**flags),
        context_window=_coerce_window(raw.get("context_window"), model),
    )


def _load() -> dict[str, DeclaredModel]:
    path = overlay_path()
    stamp = _stamp(path)
    if stamp is None:
        _cache["stamp"], _cache["entries"] = None, {}
        return {}
    if stamp == _cache["stamp"]:
        return _cache["entries"]

    entries: dict[str, DeclaredModel] = {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - a bad overlay must not break startup
        logger.warning("models.json is unreadable (%s); ignoring declared models", exc)
        _cache["stamp"], _cache["entries"] = stamp, {}
        return {}

    models = data.get("models") if isinstance(data, dict) else None
    if not isinstance(models, dict):
        logger.warning('models.json must be {"models": {"<provider:id>": {...}}}; ignoring')
        _cache["stamp"], _cache["entries"] = stamp, {}
        return {}

    for model, raw in models.items():
        if not isinstance(model, str) or not model.strip():
            continue
        model = model.strip()
        if ":" not in model:
            # Bare ids are legal and meaningful — the matrix stores OpenAI's rows that way,
            # and an endpoint configured as the `openai` provider with a custom base_url
            # serves bare names too. But a bare id where `custom:` was meant describes a
            # model nobody ever calls, and that failure is silent, so say so out loud.
            logger.info(
                "models.json: %r has no provider prefix, so it describes the default "
                "(openai) route. For a self-hosted endpoint added as a Custom provider "
                "the id must read 'custom:%s'.",
                model,
                model,
            )
        parsed = _parse_entry(model, raw)
        if parsed is not None:
            entries[model] = parsed

    _cache["stamp"], _cache["entries"] = stamp, entries
    return entries


def declared() -> dict[str, DeclaredModel]:
    """All valid declared entries, keyed by full routed id (empty when no overlay file)."""
    if os.environ.get("COWORKER_DISABLE_MODEL_OVERLAY"):
        return {}
    return _load()


def declared_entry(model: str) -> Optional[DeclaredModel]:
    return declared().get(model)


def invalidate() -> None:
    """Drop the mtime cache — for tests, and for a caller that just rewrote the file."""
    _cache["stamp"], _cache["entries"] = None, {}


__all__ = ["DeclaredModel", "declared", "declared_entry", "invalidate", "overlay_path"]
