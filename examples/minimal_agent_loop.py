#!/usr/bin/env python3
"""
minimal_agent_loop.py — Embedding LAE in a simple agent-style loop.

The smallest realistic host: an agent that scores candidate actions each
tick and acts on the best one. LAE rides sidecar — it does nothing while
the agent is decisive, and structures the crossing whenever the agent
wobbles between actions.

The loop demonstrates the key embedding pattern:

    while True:
        scores = agent.evaluate(world)          # host's own logic
        outcome = lae.observe(as_observation(scores))
        if outcome.activated:
            ...log / annotate / adapt...        # advisory only
        agent.act(best(scores))                 # host still decides

Run from the repo root:
    python examples/minimal_agent_loop.py
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

# Allow running straight from a repo checkout without pip install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lae import LAE

ACTIONS = ["gather", "build", "scout"]


def evaluate(world: dict) -> dict[str, float]:
    """Toy scoring: resources favor building, danger favors scouting."""
    r, d = world["resources"], world["danger"]
    raw = {
        "gather": max(0.05, 1.0 - r),
        "build": max(0.05, r * (1.0 - d)),
        "scout": max(0.05, d),
    }
    total = sum(raw.values())
    return {k: round(v / total, 3) for k, v in raw.items()}


def main() -> None:
    print("🤖 LAE in a minimal agent loop\n")
    rng = random.Random(11)

    lae = LAE()
    liminal_ticks: list[int] = []
    lae.events.subscribe(
        "transition.detected",
        lambda ev: liminal_ticks.append(ev["payload"]["event"].time_window.end),
    )

    world = {"resources": 0.15, "danger": 0.05}
    mode = "gathering"

    for tick in range(1, 13):
        # World drifts; mid-run a threat appears and forces a regime change.
        world["resources"] = min(1.0, world["resources"] + rng.uniform(0.04, 0.10))
        if tick == 6:
            world["danger"] = 0.5  # threat arrives — scoring flattens out
        elif tick > 6:
            world["danger"] = max(0.0, world["danger"] - 0.12)

        scores = evaluate(world)
        outcome = lae.observe({
            "state_id": f"mode::{mode}",
            "hypotheses": scores,
            "timestamp": float(tick),
        })

        chosen = max(scores, key=scores.get)
        marker = ""
        if outcome.activated:
            intent = outcome.result.intent
            lean = max(intent.vector, key=intent.vector.get) if intent.vector else "—"
            marker = f"   ⚡ liminal: leaving {outcome.result.event.source_state_id}, lean → {lean}"
        print(f"  tick {tick:2d}: scores={scores}  act={chosen}{marker}")

        mode = chosen + "ing"

    stats = lae.diagnostics.snapshot()
    print(f"\n  Observations: {stats['activation']['observations']}, "
          f"activations: {stats['activation']['activations']}, "
          f"dormancy: {stats['activation']['dormancy_ratio']:.0%}")
    print(f"  Episodes remembered: {stats['memory']['episode_count']}, "
          f"identity trajectory: {stats['identity']['trajectory_length']} points")
    print("\n  The agent decided every tick. LAE only woke for the wobbles —")
    print("  and remembers each crossing for the next one.")


if __name__ == "__main__":
    main()
