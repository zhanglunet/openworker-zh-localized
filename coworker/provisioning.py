"""First-run provisioning — seed a fresh state directory from shipped defaults.

An enterprise build wants its people to open the app and already have the right model
endpoint, approval policy, command allowlist, MCP servers and skills. None of that has a
delivery path today: config lives in ``<state-dir>``, which is created empty on first run,
and skills have no in-package channel at all (``pyproject`` only ships
``personas/builtin/*.md``), so a bundled skill folder would never reach the user.

This module is that path. A build points ``COWORKER_DEFAULTS_DIR`` at a folder it ships:

    defaults/
      config.toml        → <state-dir>/config.toml
      models.json        → <state-dir>/models.json      (see providers/model_overlay.py)
      mcp.json           → <state-dir>/mcp.json
      AGENTS.md          → <state-dir>/AGENTS.md
      skills/<name>/     → <state-dir>/skills/<name>/   (per skill, not the whole tree)

Three rules make this safe to run on **every** launch:

1. **Never overwrite.** A file that already exists is the user's, full stop. Seeding is how
   an empty slot gets filled, never how a setting gets pushed. (Policy that must *win* over
   the user belongs in a managed-config mechanism, which this deliberately is not.)
2. **Never resurrect.** Deleting a seeded skill has to stick, or the next launch quietly
   undoes the user's decision. A receipt file records what was seeded so a missing item is
   read as "removed", not as "missing".
3. **Never fatal.** A malformed defaults folder logs and moves on. Nobody should be unable
   to start their app because of a typo in a shipped config.

Per-skill (rather than whole-folder) granularity is what lets a later build add a skill
without touching the ones already there.
"""

from __future__ import annotations

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

logger = logging.getLogger("coworker.provisioning")

# Single files copied verbatim into the state dir.
SEED_FILES = ("config.toml", "models.json", "mcp.json", "AGENTS.md", ".env")
# Directories seeded entry-by-entry rather than as one blob.
SEED_TREES = ("skills",)

RECEIPT_NAME = ".provisioned.json"


def defaults_dir() -> Optional[Path]:
    """Where shipped defaults live, or None when this build ships none.

    ``COWORKER_DEFAULTS_DIR`` is how a packaged app points at a folder inside its bundle;
    ``<package>/defaults`` is the fallback for a build that vendors them into the wheel.
    """
    env = os.environ.get("COWORKER_DEFAULTS_DIR", "").strip()
    if env:
        path = Path(env).expanduser()
        return path if path.is_dir() else None
    packaged = Path(__file__).resolve().parent / "defaults"
    return packaged if packaged.is_dir() else None


def _receipt_path(state: Path) -> Path:
    return state / RECEIPT_NAME


def _load_receipt(state: Path) -> set[str]:
    try:
        data = json.loads(_receipt_path(state).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return set()
    except Exception as exc:  # noqa: BLE001 - a bad receipt just means "seed nothing new"
        logger.warning("provisioning receipt unreadable (%s); treating it as empty", exc)
        return set()
    seeded = data.get("seeded") if isinstance(data, dict) else None
    return {s for s in seeded or [] if isinstance(s, str)}


def _save_receipt(state: Path, seeded: set[str]) -> None:
    try:
        _receipt_path(state).write_text(
            json.dumps({"seeded": sorted(seeded)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except OSError as exc:
        # Without the receipt the next launch would re-seed a deleted item. Worth a warning,
        # not worth failing a startup that has otherwise succeeded.
        logger.warning("could not write the provisioning receipt: %s", exc)


def _copy_file(src: Path, dest: Path) -> bool:
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        # config.toml and .env can carry an endpoint or a key; keep them owner-only, the
        # same way secrets.py treats what it writes.
        if dest.name in ("config.toml", ".env"):
            try:
                dest.chmod(0o600)
            except OSError:
                pass
        return True
    except OSError as exc:
        logger.warning("could not seed %s: %s", dest.name, exc)
        return False


def _copy_tree(src: Path, dest: Path) -> bool:
    try:
        shutil.copytree(src, dest)
        return True
    except OSError as exc:
        logger.warning("could not seed %s: %s", dest.name, exc)
        return False


def seed_defaults(state: Optional[Path] = None, source: Optional[Path] = None) -> list[str]:
    """Fill empty slots in the state dir from shipped defaults. Returns what was seeded.

    Safe to call on every launch: existing files are left alone, and anything already
    recorded in the receipt is never re-created.
    """
    if os.environ.get("COWORKER_SKIP_PROVISIONING"):
        return []
    src = source or defaults_dir()
    if src is None:
        return []
    if state is None:
        from .secrets import state_dir

        state = state_dir()

    try:
        state.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        logger.warning("state dir unavailable (%s); skipping provisioning", exc)
        return []

    already = _load_receipt(state)
    seeded: list[str] = []

    for name in SEED_FILES:
        candidate = src / name
        if not candidate.is_file() or name in already:
            continue
        if (state / name).exists():
            # Pre-existing user file: record it so we never revisit this slot, and so a
            # later delete isn't mistaken for "never seeded".
            already.add(name)
            continue
        if _copy_file(candidate, state / name):
            seeded.append(name)
            already.add(name)

    for tree in SEED_TREES:
        tree_src = src / tree
        if not tree_src.is_dir():
            continue
        for entry in sorted(tree_src.iterdir()):
            if not entry.is_dir() or entry.name.startswith("."):
                continue
            key = f"{tree}/{entry.name}"
            if key in already:
                continue
            target = state / tree / entry.name
            if target.exists():
                already.add(key)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            if _copy_tree(entry, target):
                seeded.append(key)
                already.add(key)

    if seeded or already != _load_receipt(state):
        _save_receipt(state, already)
    if seeded:
        logger.info("provisioned defaults: %s", ", ".join(seeded))
    return seeded


__all__ = ["defaults_dir", "seed_defaults", "SEED_FILES", "SEED_TREES", "RECEIPT_NAME"]
