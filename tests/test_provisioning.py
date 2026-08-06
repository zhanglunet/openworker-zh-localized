"""First-run provisioning.

An enterprise build ships defaults (endpoint, approval policy, MCP servers, skills) and
wants them in place the first time someone opens the app. That is only safe if seeding can
never talk over the user, so these tests pin the three rules the module promises: never
overwrite, never resurrect a deleted item, never fail a startup.
"""

from __future__ import annotations

import json

import pytest

from coworker.provisioning import RECEIPT_NAME, defaults_dir, seed_defaults


@pytest.fixture
def dirs(tmp_path, monkeypatch):
    src = tmp_path / "defaults"
    (src / "skills" / "corp-expense").mkdir(parents=True)
    (src / "skills" / "corp-expense" / "SKILL.md").write_text(
        "---\nname: corp-expense\ndescription: 报销审核\n---\n步骤…", encoding="utf-8"
    )
    (src / "config.toml").write_text('model = "custom:corp"\nmode = "interactive"\n', encoding="utf-8")
    (src / "models.json").write_text(
        json.dumps({"models": {"custom:corp": {"label": "内网"}}}, ensure_ascii=False),
        encoding="utf-8",
    )
    state = tmp_path / "state"
    monkeypatch.delenv("COWORKER_SKIP_PROVISIONING", raising=False)
    return src, state


def test_seeds_an_empty_state_dir(dirs):
    src, state = dirs
    seeded = seed_defaults(state, src)
    assert set(seeded) == {"config.toml", "models.json", "skills/corp-expense"}
    assert (state / "config.toml").read_text(encoding="utf-8").startswith('model = "custom:corp"')
    assert (state / "skills" / "corp-expense" / "SKILL.md").is_file()


def test_never_overwrites_user_files(dirs):
    src, state = dirs
    state.mkdir()
    (state / "config.toml").write_text('model = "mine"\n', encoding="utf-8")
    seeded = seed_defaults(state, src)
    assert "config.toml" not in seeded
    assert (state / "config.toml").read_text(encoding="utf-8") == 'model = "mine"\n'


def test_is_idempotent(dirs):
    src, state = dirs
    assert seed_defaults(state, src)
    assert seed_defaults(state, src) == [], "a second launch must seed nothing"


def test_deleting_a_seeded_skill_sticks(dirs):
    """Without a receipt the next launch quietly undoes the user's decision."""
    src, state = dirs
    seed_defaults(state, src)
    import shutil

    shutil.rmtree(state / "skills" / "corp-expense")
    assert seed_defaults(state, src) == []
    assert not (state / "skills" / "corp-expense").exists()


def test_a_new_skill_arrives_without_touching_existing_ones(dirs):
    """Per-skill granularity: an app update can add a skill and must not disturb the rest."""
    src, state = dirs
    seed_defaults(state, src)
    (state / "skills" / "corp-expense" / "SKILL.md").write_text("用户改过了", encoding="utf-8")

    (src / "skills" / "corp-onboarding").mkdir()
    (src / "skills" / "corp-onboarding" / "SKILL.md").write_text(
        "---\nname: corp-onboarding\ndescription: 入职\n---\n", encoding="utf-8"
    )
    seeded = seed_defaults(state, src)
    assert seeded == ["skills/corp-onboarding"]
    assert (state / "skills" / "corp-expense" / "SKILL.md").read_text(encoding="utf-8") == "用户改过了"


def test_preexisting_file_is_recorded_so_a_later_delete_sticks(dirs):
    """A user who had a config before the first provisioned launch, then deletes it, must
    not have it reappear — the slot was never ours to fill."""
    src, state = dirs
    state.mkdir()
    (state / "config.toml").write_text("mine\n", encoding="utf-8")
    seed_defaults(state, src)
    (state / "config.toml").unlink()
    assert seed_defaults(state, src) == []
    assert not (state / "config.toml").exists()


def test_seeded_config_is_owner_only(dirs):
    """config.toml can carry an endpoint (and .env a key) — same treatment as secrets.py."""
    src, state = dirs
    seed_defaults(state, src)
    mode = (state / "config.toml").stat().st_mode & 0o777
    assert mode == 0o600, oct(mode)


def test_no_defaults_is_a_no_op(tmp_path):
    assert seed_defaults(tmp_path / "state", tmp_path / "missing") == []
    assert not (tmp_path / "state" / RECEIPT_NAME).exists()


def test_kill_switch(dirs, monkeypatch):
    src, state = dirs
    monkeypatch.setenv("COWORKER_SKIP_PROVISIONING", "1")
    assert seed_defaults(state, src) == []


def test_unreadable_receipt_does_not_crash(dirs):
    src, state = dirs
    seed_defaults(state, src)
    (state / RECEIPT_NAME).write_text("{ broken", encoding="utf-8")
    # Receipt gone → the slots look unseeded, but the files are still there, so the
    # never-overwrite rule keeps them intact and nothing is duplicated.
    assert seed_defaults(state, src) == []
    assert (state / "config.toml").is_file()


def test_unreadable_source_entry_is_skipped_not_fatal(dirs):
    src, state = dirs
    (src / "skills" / "not-a-dir.txt").write_text("x", encoding="utf-8")
    seeded = seed_defaults(state, src)
    assert "skills/corp-expense" in seeded
    assert not any("not-a-dir" in s for s in seeded)


def test_defaults_dir_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("COWORKER_DEFAULTS_DIR", str(tmp_path))
    assert defaults_dir() == tmp_path
    monkeypatch.setenv("COWORKER_DEFAULTS_DIR", str(tmp_path / "nope"))
    assert defaults_dir() is None


def test_seeded_skill_is_discoverable(dirs):
    """The whole point of seeding skills: SkillLoader must find them afterwards."""
    src, state = dirs
    seed_defaults(state, src)
    from coworker.skills.base import SkillLoader

    loader = SkillLoader([state / "skills"])
    assert "corp-expense" in loader.names()
    assert loader.get("corp-expense").description == "报销审核"


def test_seeded_models_json_reaches_the_matrix(dirs, monkeypatch):
    """And the seeded model declaration must be the one the runtime reads."""
    src, state = dirs
    seed_defaults(state, src)
    from coworker.providers import matrix, model_overlay

    monkeypatch.setattr(model_overlay, "overlay_path", lambda: state / "models.json")
    model_overlay.invalidate()
    try:
        assert matrix.entry_for("custom:corp").label == "内网"
    finally:
        model_overlay.invalidate()
