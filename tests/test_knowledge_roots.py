"""Standing knowledge roots (`knowledge_roots` in the global config).

A shared reference corpus — runbooks, policies, a synced knowledge drive — should be
readable in every conversation without someone re-adding the folder each time. That is a
capability grant, so the tests here are mostly about what it must NOT do: never writable,
never declarable by a checked-out repo, never outliving the config line that created it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from coworker.config import _GLOBAL_ONLY_FIELDS, load_config
from coworker.server.manager import SessionManager


@pytest.fixture
def kb(tmp_path):
    corpus = tmp_path / "CorpKB"
    (corpus / "runbooks").mkdir(parents=True)
    (corpus / "runbooks" / "restart.md").write_text("重启步骤…", encoding="utf-8")
    return corpus


def _global_config(tmp_path, body: str) -> Path:
    path = tmp_path / "config.toml"
    path.write_text(body, encoding="utf-8")
    return path


def test_config_parses_knowledge_roots(tmp_path, kb):
    cfg = load_config(global_path=_global_config(tmp_path, f'knowledge_roots = ["{kb}"]\n'))
    assert cfg.knowledge_roots == [str(kb)]


def test_defaults_to_empty(tmp_path):
    assert load_config(global_path=_global_config(tmp_path, "model = 'x'\n")).knowledge_roots == []


def test_a_workspace_config_cannot_grant_itself_read_access(tmp_path, kb):
    """The important one. A cloned repo declaring `knowledge_roots = ["~/.ssh"]` would be
    handing itself a key, so this field is global-config-only, like allowed_commands."""
    assert "knowledge_roots" in _GLOBAL_ONLY_FIELDS

    workspace = tmp_path / "repo"
    (workspace / ".coworker").mkdir(parents=True)
    (workspace / ".coworker" / "config.toml").write_text(
        f'knowledge_roots = ["{kb}"]\n', encoding="utf-8"
    )
    cfg = load_config(
        workspace,
        global_path=_global_config(tmp_path, "model = 'x'\n"),
        workspace_trusted=True,  # even trusted: this is a grant, not a preference
    )
    assert cfg.knowledge_roots == []


def test_mounted_read_only_and_deduped(tmp_path, kb, monkeypatch):
    monkeypatch.setattr(
        "coworker.server.manager.load_config",
        lambda *a, **k: type("C", (), {"knowledge_roots": [str(kb), str(kb)]})(),
    )
    mounted = SessionManager._knowledge_roots(tmp_path / "scratch", [])
    assert len(mounted) == 1, "the same folder must not mount twice"
    assert mounted[0]["writable"] is False, "a standing shared grant is never writable"
    assert mounted[0]["label"] == "CorpKB"


def test_missing_folder_is_skipped_not_fatal(tmp_path, monkeypatch):
    """A sync client mid-download, or a folder that only exists on some machines, must not
    stop a session from starting."""
    monkeypatch.setattr(
        "coworker.server.manager.load_config",
        lambda *a, **k: type("C", (), {"knowledge_roots": ["/nope/missing"]})(),
    )
    assert SessionManager._knowledge_roots(tmp_path, []) == []


def test_does_not_duplicate_the_scratch_or_a_hand_added_folder(tmp_path, kb, monkeypatch):
    monkeypatch.setattr(
        "coworker.server.manager.load_config",
        lambda *a, **k: type("C", (), {"knowledge_roots": [str(kb), str(tmp_path)]})(),
    )
    already = [{"path": str(kb), "writable": True, "label": "kb"}]
    mounted = SessionManager._knowledge_roots(tmp_path, already)
    # kb was added by hand, tmp_path IS the scratch — neither may be mounted again
    assert mounted == []


def test_config_managed_roots_are_not_persisted_as_session_folders(tmp_path, kb, monkeypatch):
    """Otherwise they outlive the config entry: removing the line would leave sessions with
    standing read access to a corpus the admin took away."""
    from coworker.roots import RootDir

    monkeypatch.setattr(
        "coworker.server.manager.load_config",
        lambda *a, **k: type("C", (), {"knowledge_roots": [str(kb)]})(),
    )
    user_folder = tmp_path / "mine"
    user_folder.mkdir()
    engine = type(
        "E",
        (),
        {
            "roots": [
                RootDir(path=tmp_path / "scratch", writable=True, label="scratch"),
                RootDir(path=user_folder, writable=True),
                RootDir(path=kb, writable=False),
            ]
        },
    )()
    persisted = SessionManager._extra_roots_of(engine)
    paths = {Path(r["path"]).resolve() for r in persisted}
    assert user_folder.resolve() in paths, "a hand-added folder must still be remembered"
    assert kb.resolve() not in paths, "the config-managed corpus must not be persisted"
