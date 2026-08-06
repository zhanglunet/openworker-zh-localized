"""Catalog policy — narrowing the connector / provider surface.

The point of these tests is that **hiding is not enforcing**. A policy that only filters
the listing would leave every other path open: an already-stored profile, a hand-written
API call, a config still naming a denied vendor. So each enforcement point is pinned
separately, and the listing filter is pinned for the second thing it does — the agent's
toolset is assembled from that same listing.
"""

from __future__ import annotations

import pytest

from coworker.catalog_policy import (
    connector_permitted,
    model_permitted,
    provider_permitted,
)


class Cfg:
    def __init__(self, **kw):
        self.allowed_connectors = kw.get("allowed_connectors", [])
        self.denied_connectors = kw.get("denied_connectors", [])
        self.allowed_providers = kw.get("allowed_providers", [])
        self.denied_providers = kw.get("denied_providers", [])


def test_unrestricted_by_default():
    cfg = Cfg()
    assert connector_permitted("gmail", cfg) and provider_permitted("openai", cfg)


def test_allowlist_excludes_everything_else():
    cfg = Cfg(allowed_connectors=["github", "jira"])
    assert connector_permitted("github", cfg)
    assert not connector_permitted("gmail", cfg)


def test_denylist_without_an_allowlist():
    cfg = Cfg(denied_connectors=["gmail"])
    assert not connector_permitted("gmail", cfg)
    assert connector_permitted("github", cfg)


def test_deny_wins_over_allow():
    """A contradictory policy must resolve the safe way, not the permissive way."""
    cfg = Cfg(allowed_connectors=["gmail"], denied_connectors=["gmail"])
    assert not connector_permitted("gmail", cfg)


@pytest.mark.parametrize("name", ["GitHub", " github ", "GITHUB"])
def test_matching_is_case_and_space_insensitive(name):
    assert connector_permitted(name, Cfg(allowed_connectors=["github"]))


def test_model_id_is_checked_by_its_provider_prefix():
    cfg = Cfg(allowed_providers=["custom", "ollama"])
    assert model_permitted("custom:qwen3-72b", cfg) is None
    assert model_permitted("anthropic:claude-x", cfg) is not None


def test_bare_model_id_is_checked_against_openai():
    """A bare id routes to the OpenAI default, so a policy that denies openai must catch it
    — otherwise `gpt-5.6-sol` would slip straight past a provider allowlist."""
    cfg = Cfg(allowed_providers=["custom"])
    assert model_permitted("gpt-5.6-sol", cfg) is not None


def test_refusal_names_the_policy():
    """A user who can see the entry in a screenshot deserves a real reason, not a 404."""
    message = model_permitted("anthropic:claude", Cfg(denied_providers=["anthropic"]))
    assert "策略" in message and "anthropic" in message


# -- enforcement points ---------------------------------------------------------


def test_listing_filter_also_removes_the_agent_toolset(monkeypatch, tmp_path):
    """connector_list feeds BOTH the UI and agent._enabled_connector_tools, so filtering
    there is what makes a denied connector unreachable rather than merely invisible."""
    from coworker.connectors import setup
    from coworker.secrets import SecretStore

    secrets = SecretStore(tmp_path / "secrets.json")
    monkeypatch.setattr(
        "coworker.catalog_policy._config", lambda: Cfg(allowed_connectors=["github"])
    )
    names = {c["name"] for c in setup.connector_list(secrets)}
    assert names == {"github"} or names <= {"github"}, names
    assert "gmail" not in names


def test_connect_is_refused_even_with_a_stored_profile(monkeypatch, tmp_path):
    from coworker.connectors import setup
    from coworker.secrets import SecretStore

    secrets = SecretStore(tmp_path / "secrets.json")
    monkeypatch.setattr(
        "coworker.catalog_policy._config", lambda: Cfg(denied_connectors=["github"])
    )
    res = setup.connect_connector(secrets, "github", {"token": "x"}, validate=False)
    assert res["ok"] is False and "策略" in res["error"]


def test_provider_client_build_is_refused(monkeypatch):
    """The single funnel every model call passes through — a session already pointed at a
    now-denied vendor must stop working, not keep working because the listing changed."""
    from coworker.providers import registry

    monkeypatch.setattr(
        "coworker.catalog_policy._config", lambda: Cfg(denied_providers=["anthropic"])
    )
    with pytest.raises(PermissionError) as exc:
        registry.build_provider_client("anthropic", {"api_key": "x"}, None)
    assert "anthropic" in str(exc.value)


def test_provider_descriptors_are_filtered(monkeypatch):
    from coworker.providers import registry

    monkeypatch.setattr(
        "coworker.catalog_policy._config", lambda: Cfg(allowed_providers=["custom", "ollama"])
    )
    names = {d.name for d in registry.provider_descriptors()}
    assert names == {"custom", "ollama"}


def test_unrestricted_policy_leaves_the_catalog_untouched(monkeypatch):
    from coworker.providers import registry

    monkeypatch.setattr("coworker.catalog_policy._config", lambda: Cfg())
    assert len(registry.provider_descriptors()) == len(registry.DESCRIPTORS)
