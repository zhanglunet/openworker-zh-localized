"""Configuration — layered TOML: built-in defaults < global < per-workspace.

Global:    <state-dir>/config.toml   (see `secrets.state_dir`; platform-native)
Workspace: <workspace>/.coworker/config.toml   (overrides global)

Workspace command allowances apply only after the user trusts that exact canonical
workspace path. Other permission grants remain global-only.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .secrets import state_dir

# Commands auto-run WITHOUT an approval prompt. There is no generally safe executable:
# nominally read-only programs can read secrets outside the workspace, expand environment
# variables, load project-controlled config/plugins, or execute helpers (for example
# `find -exec` and pytest collection). Keep the built-in list empty. A user may explicitly
# opt into command prefixes in their user-owned global config, accepting that authority.
DEFAULT_ALLOWED_COMMANDS: list[str] = []


@dataclass
class Config:
    model: str = "gpt-5.6-sol"
    mode: str = "interactive"
    max_iterations: int = 150
    allowed_commands: list[str] = field(
        default_factory=lambda: list(DEFAULT_ALLOWED_COMMANDS)
    )
    # In "custom" permission mode, these tools are auto-approved (e.g. file edits)
    # while everything else still asks.
    auto_allow: list[str] = field(default_factory=list)
    # Folders mounted READ-ONLY into every knowledge-work session, on top of its scratch
    # root and whatever the user added by hand. This is how a shared reference corpus (an
    # ops runbook tree, a synced policy folder) is available in every conversation without
    # someone re-adding it each time. Paths that don't exist are skipped silently — a
    # sync client that hasn't finished, or a folder mounted only on some machines, must
    # not break session creation.
    knowledge_roots: list[str] = field(default_factory=list)
    # Catalog policy — which connectors / model providers this installation may use.
    # Empty allowlist = no restriction; a name in both lists is denied (deny wins).
    # See catalog_policy.py; global-only for the same reason as allowed_commands.
    allowed_connectors: list[str] = field(default_factory=list)
    denied_connectors: list[str] = field(default_factory=list)
    allowed_providers: list[str] = field(default_factory=list)
    denied_providers: list[str] = field(default_factory=list)
    # Audit forwarding to an enterprise log sink (SIEM). Empty url = off. See
    # audit_forward.py: background-threaded, bounded queue, fails open — the local audit
    # log stays the source of truth and a down collector never blocks a turn.
    audit_forward_url: str = ""
    audit_forward_token: str = ""   # "${CORP_SIEM_TOKEN}" resolves from the environment
    audit_forward_batch: int = 50
    audit_forward_timeout: float = 5.0
    host: str = "127.0.0.1"
    port: int = 8765
    # Web search provider: "duckduckgo" (keyless default) | "tavily" | "brave" (need a key).
    web_search_provider: str = "duckduckgo"
    # OpenWorker Cloud (sign-in + managed connectors). Config, never constants:
    # dev/staging/BYO-VPC deployments point these at their own instances.
    cloud_base_url: str = "https://api.openworker.com"
    # Auth0 tenant + API audience are registered identifiers, not branding: the
    # tenant name can never be renamed, and the audience must match the API
    # identifier registered in Auth0 — both keep the legacy value on purpose.
    cloud_auth_domain: str = "opencoworker.us.auth0.com"
    cloud_client_id: str = "g1l4Q1lhYWmyS03qPSf4KEJGrgq02Qam"
    cloud_audience: str = "https://api.opencoworker.app"
    # Managed relay WebSocket endpoint (Slack/GitHub inbound). Defaults to the
    # PRODUCTION relay so a fresh install relays out of the box — an empty
    # default shipped once as "connected but relay OFF" on every machine
    # without a hand-edited config.toml. Empty override ⇒ relay disabled
    # (manual Socket Mode still works); dev/BYO deployments point elsewhere.
    cloud_relay_ws_url: str = (
        "wss://l4z1paxb83.execute-api.us-east-1.amazonaws.com/ocw-connect"
    )


_FIELDS = {
    "model",
    "mode",
    "max_iterations",
    "allowed_commands",
    "auto_allow",
    "knowledge_roots",
    "allowed_connectors",
    "denied_connectors",
    "allowed_providers",
    "denied_providers",
    "audit_forward_url",
    "audit_forward_token",
    "audit_forward_batch",
    "audit_forward_timeout",
    "host",
    "port",
    "web_search_provider",
    "cloud_base_url",
    "cloud_auth_domain",
    "cloud_client_id",
    "cloud_audience",
    "cloud_relay_ws_url",
}

# These fields change what consequential actions can run without a prompt, so the normal
# workspace override pass never applies them. `allowed_commands` is added separately only
# for a canonically trusted workspace; `auto_allow` remains user-global only.
# `knowledge_roots` is here for the same reason in reverse: it GRANTS read access to
# folders outside the workspace, so a checked-out repo must never be able to declare one
# (`knowledge_roots = ["~/.ssh"]` in a project config would otherwise be a handed-over key).
_GLOBAL_ONLY_FIELDS = {
    "allowed_commands",
    "auto_allow",
    "knowledge_roots",
    # Catalog policy decides what may leave the machine; a checked-out repo widening it
    # would defeat the point.
    "allowed_connectors",
    "denied_connectors",
    "allowed_providers",
    "denied_providers",
    # Where activity data is shipped is not a per-project preference.
    "audit_forward_url",
    "audit_forward_token",
    "audit_forward_batch",
    "audit_forward_timeout",
}
_WORKSPACE_FIELDS = _FIELDS - _GLOBAL_ONLY_FIELDS


def global_config_path() -> Path:
    return state_dir() / "config.toml"


def _read(path: Path) -> dict[str, Any]:
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except (OSError, tomllib.TOMLDecodeError):
        return {}


def workspace_allowed_commands(workspace: str | Path) -> list[str]:
    """Command prefixes requested by repository config; advisory until workspace trust."""
    path = Path(workspace).expanduser() / ".coworker" / "config.toml"
    value = _read(path).get("allowed_commands", [])
    if not isinstance(value, list):
        return []
    return list(dict.fromkeys(v.strip() for v in value if isinstance(v, str) and v.strip()))


def load_config(
    workspace: Optional[str | Path] = None,
    *,
    global_path: Optional[Path] = None,
    workspace_trusted: bool = False,
) -> Config:
    cfg = Config()

    g = Path(global_path) if global_path is not None else global_config_path()
    if g.is_file():
        for key, value in _read(g).items():
            if key in _FIELDS:
                setattr(cfg, key, value)
    if workspace:
        w = Path(workspace).expanduser() / ".coworker" / "config.toml"
        if w.is_file():
            for key, value in _read(w).items():
                if key in _WORKSPACE_FIELDS:
                    setattr(cfg, key, value)
            if workspace_trusted:
                cfg.allowed_commands = list(
                    dict.fromkeys(
                        [*cfg.allowed_commands, *workspace_allowed_commands(workspace)]
                    )
                )
    return cfg
