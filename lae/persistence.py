"""
lae.persistence — Durable state for memory and identity.

Everything in LAE is in-memory by default: episodes, the signature
index, and the identity gradient all die with the process. This module
gives the engine a presence that survives restarts — the crossings it
remembers and the identity it has become are written to a single JSON
file and restored into a fresh engine on the next boot.

Stdlib only (json + os.replace), per the zero-dependency rule. Writes
are atomic: state is written to a temp file in the same directory and
moved into place, so a crash mid-save can never corrupt an existing
state file.

What persists (durable state):
- every LiminalMemoryEpisode, with store metadata and insertion order
- the identity gradient (invariants, rigidity, plasticity zones,
  drift vectors, full trajectory_history) and its tracker internals
- ID counter floors, so episode/anchor IDs keep increasing across
  process lifetimes instead of colliding with remembered ones

What deliberately does not persist:
- detector observation history (the oscillation window is milliseconds
  wide — stale the moment the process exits)
- hooks, event subscriptions, diagnostics counters (host wiring, not
  engine state)

Usage (usually via the LAE external API rather than directly):

    from lae.persistence import save_state, load_state

    save_state(engine, "lae_state.json")
    ...
    state = load_state("lae_state.json")   # None if no file yet
    if state is not None:
        engine.restore_state(state["engine"])
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .pipeline import LiminalAnchorEngine

FORMAT_NAME = "lae-state"
FORMAT_VERSION = 1


class StateFileError(ValueError):
    """Raised when a state file exists but cannot be understood."""


def save_state(engine: LiminalAnchorEngine, path: str | Path) -> Path:
    """Atomically write one engine's durable state to a JSON file.

    Returns the path written. Parent directories are created as needed.
    """
    return _write_document({"engine": engine.export_state()}, path)


def save_collective_state(
    engines: dict[str, LiminalAnchorEngine], path: str | Path
) -> Path:
    """Atomically write a multi-mind roster's durable state to one file.

    Each agent's engine state is stored under its agent ID. Minds stay
    separate on disk exactly as they do in memory (Phase 4: identity is
    never merged).
    """
    return _write_document(
        {"agents": {aid: eng.export_state() for aid, eng in engines.items()}},
        path,
    )


def _write_document(payload: dict[str, Any], path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    document = {
        "format": FORMAT_NAME,
        "version": FORMAT_VERSION,
        "saved_at": time.time(),
        **payload,
    }

    # Write to a temp file in the target directory, then move into
    # place — os.replace is atomic on the same filesystem, so a crash
    # mid-write never leaves a half-written state file behind.
    fd, tmp_name = tempfile.mkstemp(
        prefix=path.name + ".", suffix=".tmp", dir=path.parent
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(document, f, indent=2)
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise
    return path


def load_state(path: str | Path) -> dict[str, Any] | None:
    """Read a state file. Returns None if the file does not exist.

    Raises StateFileError if the file exists but is not valid LAE state
    — a missing memory is a fresh start, but a corrupted one should
    never be silently discarded.
    """
    path = Path(path)
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            document = json.load(f)
    except (json.JSONDecodeError, OSError) as exc:
        raise StateFileError(f"cannot read state file {path}: {exc}") from exc

    if not isinstance(document, dict) or document.get("format") != FORMAT_NAME:
        raise StateFileError(f"{path} is not an LAE state file")
    if int(document.get("version", 0)) > FORMAT_VERSION:
        raise StateFileError(
            f"{path} was written by a newer LAE (state version "
            f"{document.get('version')}, this build reads <= {FORMAT_VERSION})"
        )
    if "engine" not in document and "agents" not in document:
        raise StateFileError(f"{path} has no engine state")
    return document


def restore_into(engine: LiminalAnchorEngine, path: str | Path) -> bool:
    """Load a single-engine state file into an engine. Returns True if
    state was restored, False if no file existed (fresh start)."""
    document = load_state(path)
    if document is None:
        return False
    if "engine" not in document:
        raise StateFileError(
            f"{path} holds a multi-mind roster, not a single engine; "
            "use restore_collective_into"
        )
    engine.restore_state(document["engine"])
    return True


def restore_collective_into(
    engines: dict[str, LiminalAnchorEngine], path: str | Path
) -> bool:
    """Load a multi-mind state file into a roster of engines.

    Matching is by agent ID: agents present in both file and roster are
    restored; roster agents missing from the file start fresh; file
    agents missing from the roster are left on disk untouched (they are
    not lost — the next save from this roster will drop them, which is
    the roster owner's call to make by saving).

    Returns True if any agent was restored, False if no file existed.
    """
    document = load_state(path)
    if document is None:
        return False
    if "agents" not in document:
        raise StateFileError(
            f"{path} holds a single engine, not a multi-mind roster; "
            "use restore_into"
        )
    restored_any = False
    for agent_id, engine in engines.items():
        state = document["agents"].get(agent_id)
        if state is not None:
            engine.restore_state(state)
            restored_any = True
    return restored_any
