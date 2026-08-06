"""Catalog policy — which connectors and model providers this installation may use.

The built-in catalogs are broad on purpose: Gmail, Slack, Notion, a dozen model vendors.
A deployment with data-residency rules needs a smaller surface — not because those
integrations are bad, but because "the agent could have sent that to a US SaaS" is a
question somebody has to be able to answer with "no, it can't".

Policy lives in the GLOBAL config (never a workspace one — it decides what may leave the
machine, so a checked-out repo must not be able to widen it):

    allowed_connectors = ["github", "jira"]     # empty/absent = no restriction
    denied_connectors  = ["gmail", "slack"]     # applied after the allowlist
    allowed_providers  = ["custom", "ollama"]
    denied_providers   = ["openai", "anthropic"]

Two properties this module exists to guarantee:

* **Hiding is not enforcing.** Filtering the listing alone would be theatre: the tools are
  assembled from the same listing (``agent._enabled_connector_tools``), but connecting and
  building a client are separate paths. Both are checked here too, so a denied entry cannot
  be reached by an already-stored profile, a hand-written config, or a stale session.
* **Deny wins.** An entry in both lists is denied. Anything else makes the safer reading of
  a contradictory policy the surprising one.
"""

from __future__ import annotations

from typing import Optional

_UNRESTRICTED: tuple[str, ...] = ()


def _norm(values) -> set[str]:
    return {str(v).strip().lower() for v in (values or []) if str(v).strip()}


class _Policy:
    __slots__ = ("allowed", "denied")

    def __init__(self, allowed, denied):
        self.allowed = _norm(allowed)
        self.denied = _norm(denied)

    def permits(self, name: str) -> bool:
        key = (name or "").strip().lower()
        if not key:
            return False
        if key in self.denied:
            return False  # checked first: deny wins over an allowlist entry
        if self.allowed and key not in self.allowed:
            return False
        return True

    @property
    def active(self) -> bool:
        return bool(self.allowed or self.denied)


def _config():
    from .config import load_config

    return load_config()


def connector_policy(cfg=None) -> _Policy:
    cfg = cfg or _config()
    return _Policy(
        getattr(cfg, "allowed_connectors", _UNRESTRICTED),
        getattr(cfg, "denied_connectors", _UNRESTRICTED),
    )


def provider_policy(cfg=None) -> _Policy:
    cfg = cfg or _config()
    return _Policy(
        getattr(cfg, "allowed_providers", _UNRESTRICTED),
        getattr(cfg, "denied_providers", _UNRESTRICTED),
    )


def connector_permitted(name: str, cfg=None) -> bool:
    return connector_policy(cfg).permits(name)


def provider_permitted(name: str, cfg=None) -> bool:
    return provider_policy(cfg).permits(name)


def refusal(kind: str, name: str) -> str:
    """The message a blocked attempt returns. Names the policy rather than pretending the
    thing doesn't exist — a user who can see it in a screenshot deserves a real reason."""
    what = "连接器" if kind == "connector" else "模型服务商"
    return (
        f"{what} {name} 已被本机策略停用"
        f"（全局配置 config.toml 的 allowed_{kind}s / denied_{kind}s）。"
        "如需启用请联系管理员。"
    )


def model_permitted(model: str, cfg=None) -> Optional[str]:
    """None when the model's provider is allowed, else the refusal message.

    A model id carries its provider as a prefix (``custom:qwen3``); a bare id routes to the
    OpenAI default, so it is checked against ``openai``.
    """
    prefix = model.split(":", 1)[0] if ":" in (model or "") else "openai"
    policy = provider_policy(cfg)
    if policy.permits(prefix):
        return None
    return refusal("provider", prefix)


__all__ = [
    "connector_permitted",
    "connector_policy",
    "model_permitted",
    "provider_permitted",
    "provider_policy",
    "refusal",
]
