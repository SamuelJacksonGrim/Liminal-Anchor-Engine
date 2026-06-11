#!/usr/bin/env python3
"""
multi_mind_demo.py — Phase 4: collective transitions across multiple minds.

Three agents observe the same situation through their own full pipelines
(own detectors, own memory, own identity — minds stay separate). When two
or more destabilize at once, the coordinator builds the collective layer:
a merged TransitionEvent, a shared AmbiguityField, and a collective
ProtoIntent. Identity is never merged — provenance is preserved.

Run from the repo root:
    python examples/multi_mind_demo.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running straight from a repo checkout without pip install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lae import LAE


def main() -> None:
    print("🧠🧠🧠 LAE Multi-Mind Demonstration (Phase 4)\n")

    engine = LAE(
        agents=["analyst", "skeptic", "explorer"],
        trust_weights={"analyst": 1.0, "skeptic": 1.2, "explorer": 0.8},
    )

    # Subscribers receive the event envelope: {type, seq, timestamp, payload}.
    collective_events: list[list[str]] = []
    engine.events.subscribe(
        "collective.activated",
        lambda event: collective_events.append(event["payload"]["agents"]),
    )

    # --- Round 1: only one mind destabilizes — no collective layer. ----
    print(">>> Round 1: only the explorer wobbles")
    result = engine.observe_collective({
        "analyst": {"state_id": "report_v1", "hypotheses": {"keep": 0.9, "redo": 0.05}},
        "skeptic": {"state_id": "report_v1", "hypotheses": {"keep": 0.88, "redo": 0.06}},
        "explorer": {"state_id": "report_v1", "hypotheses": {"keep": 0.34, "redo": 0.33}},
    })
    if result:
        print(f"    triggered: {result.triggered_agents}")
        print(f"    collective layer built: {result.is_collective}\n")

    # --- Round 2: shared destabilization — the collective layer fires. -
    print(">>> Round 2: contradictory evidence lands, all three wobble")
    result = engine.observe_collective({
        "analyst": {"state_id": "report_v1", "hypotheses": {"keep": 0.36, "redo": 0.35}},
        "skeptic": {"state_id": "report_v1", "hypotheses": {"keep": 0.30, "redo": 0.38}},
        "explorer": {"state_id": "report_v1", "hypotheses": {"keep": 0.20, "redo": 0.39}},
    })
    if result and result.is_collective:
        print(f"    triggered: {result.triggered_agents}")
        print(f"    merged event source : {result.merged_event.source_state_id}")
        print(f"    merged candidates   : {result.merged_event.candidate_target_states}")
        print(f"    shared field regions: {len(result.shared_field.regions)}")
        print(f"    collective intent   : magnitude={result.collective_intent.magnitude}")
        print(f"    per-agent results preserved: {sorted(result.agent_results)}")

    print(f"\n    collective.activated events emitted: {len(collective_events)}")

    # Per-agent identity stays separate (Phase 4 design decision).
    for agent in ["analyst", "skeptic", "explorer"]:
        diag = engine.diagnostics_for(agent)
        snap = diag.snapshot()
        print(f"    {agent:9s} identity trajectory length: "
              f"{snap['identity']['trajectory_length']}")

    print("\n🎉 Multi-mind demo complete — minds merged their crossing, not themselves.")


if __name__ == "__main__":
    main()
