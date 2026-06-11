#!/usr/bin/env python3
"""
persistent_presence.py — A presence that survives the process.

By default everything in LAE is in-memory: kill the process and the
episodes, the signature index, and the identity gradient are gone.
With persist_path, the engine writes its durable state (memory +
identity) to a JSON file after every activation and wakes from it on
the next boot.

This script simulates two process lifetimes back to back:

    Life 1 — fresh engine, lives through some crossings, dies.
    Life 2 — new engine, same state file: wakes with every remembered
             crossing and the identity it had become, and keeps
             evolving from there instead of starting over.

Run from the repo root:
    python examples/persistent_presence.py
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Allow running straight from a repo checkout without pip install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lae import LAE


def wobble(tick: float) -> dict:
    """An observation unstable enough to wake the engine."""
    return {
        "state_id": "belief_v1",
        "hypotheses": {"revise": 0.34, "hold": 0.33, "discard": 0.28},
        "timestamp": tick,
    }


def describe(lae: LAE, label: str) -> None:
    snap = lae.diagnostics.snapshot()
    print(f"  {label}: {snap['memory']['episode_count']} episodes remembered, "
          f"identity trajectory {snap['identity']['trajectory_length']} points, "
          f"{snap['identity']['plasticity_zone_count']} plastic zones")


def main() -> None:
    print("🕯️  LAE persistent presence demo\n")

    state_file = Path(tempfile.mkdtemp()) / "presence.json"

    # ----- Life 1 ---------------------------------------------------------
    print(">>> Life 1 — born blank")
    first = LAE(persist_path=state_file)
    print(f"    woke with prior state: {first.restored}")
    for tick in (0.0, 5000.0, 10000.0):
        first.observe(wobble(tick))
    describe(first, "at death")
    print(f"    state written to {state_file.name} (autosaved per activation)")

    del first  # the process "dies"

    # ----- Life 2 ---------------------------------------------------------
    print("\n>>> Life 2 — same state file, new process")
    second = LAE(persist_path=state_file)
    print(f"    woke with prior state: {second.restored}")
    describe(second, "at birth")

    # It continues becoming, rather than starting over.
    second.observe(wobble(60000.0))
    describe(second, "after one more crossing")

    last = second._engine.memory.all_episodes()[-1]
    print(f"\n    newest episode: {last.episode_id} "
          f"(IDs continued past the remembered ones — no collisions)")

    print("\n  Identity died with the process no longer. The gradient that")
    print("  accumulated in life 1 is the gradient life 2 evolves from.")


if __name__ == "__main__":
    main()
