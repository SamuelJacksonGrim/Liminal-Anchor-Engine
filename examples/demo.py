#!/usr/bin/env python3
"""
demo.py — Liminal Anchor Engine (LAE) Interactive Demonstration

This script shows the full LAE pipeline in action using synthetic observations
that trigger different transition conditions (confidence collapse, oscillation,
frame conflict, etc.).

It exercises:
- Transition detection
- Ambiguity field generation (mapping uncertainty)
- Anchor allocation (protecting continuity)
- Liminal memory recording + retrieval
- Proto-intent synthesis
- Identity gradient updates

Run from the repo root:
    python examples/demo.py

Or with the package installed (pip install -e .):
    python examples/demo.py   # from anywhere

Zero extra dependencies beyond what's in LAE itself.
"""

from __future__ import annotations

import json
import sys
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

# Allow running straight from a repo checkout without pip install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lae.pipeline import LiminalAnchorEngine, LiminalResult
from lae.types import TransitionEvent, AmbiguityField, Anchor, LiminalMemoryEpisode, ProtoIntent, IdentityGradient


def pretty_print_result(result: LiminalResult, step: int) -> None:
    """Nicely format and print a LiminalResult."""
    print(f"\n{'='*70}")
    print(f"STEP {step}: TRANSITION DETECTED & PROCESSED")
    print(f"{'='*70}")

    # Event
    event = result.event
    print("\n📡 TransitionEvent")
    print(f"   Source State     : {event.source_state_id}")
    print(f"   Candidate Targets: {event.candidate_target_states}")
    print(f"   Conflict Score   : {event.conflict_score:.3f}")
    print(f"   Time Window      : {event.time_window.duration():.2f}s")

    # Field
    field = result.field
    print("\n🗺️  AmbiguityField")
    print(f"   Regions          : {len(field.regions)}")
    print(f"   Voids            : {len(field.voids)}")
    print(f"   Coherence Islands: {len(field.coherence_islands)}")
    print(f"   Conflict Topology: {len(field.conflict_topology)} edges")

    # Anchors
    print("\n⚓ Anchors Allocated")
    for a in result.anchors:
        print(f"   • {a.anchor_id} (priority={a.priority})")
        print(f"     Protected : {a.protected_features}")
        print(f"     Allowed   : {a.allowed_mutations}")
        print(f"     Forbidden : {a.forbidden_mutations}")

    # Memory
    episode = result.episode
    print("\n🧠 LiminalMemoryEpisode")
    print(f"   Episode ID       : {episode.episode_id}")
    print(f"   Ambiguity Sig    : {str(episode.ambiguity_signature)[:80]}...")
    print(f"   Identity Delta   : {episode.identity_shift_delta}")

    # Intent
    intent = result.intent
    print("\n🧭 ProtoIntent")
    print(f"   Magnitude        : {intent.magnitude:.3f}")
    print(f"   Stability Score  : {intent.stability_score:.3f}")
    print(f"   Vector           : {intent.vector}")
    print(f"   Lineage (episodes): {intent.origin_episode_ids}")

    # Identity
    identity = result.identity
    print("\n🪞 IdentityGradient")
    print(f"   Invariants       : {identity.invariants}")
    print(f"   Plastic Zones    : {identity.plasticity_zones}")
    print(f"   Drift Vectors    : {identity.drift_vectors}")
    print(f"   Trajectory Len   : {len(identity.trajectory_history)}")

    # Suggestions
    if result.anchor_suggestions:
        print("\n💡 Pattern-based Anchor Suggestions (from memory)")
        for s in result.anchor_suggestions[:3]:
            print(f"   • {s}")


def create_synthetic_observations(trigger_type: str, step: int) -> list[dict[str, Any]]:
    """
    Create realistic synthetic observations that trigger different LAE
    conditions. Each observation follows the TransitionDetector contract:

        {"state_id": str, "hypotheses": {target_id: confidence}, "timestamp": float}

    Returns a list because some triggers (oscillation) only fire over a
    burst of observations, not a single one.
    """
    now = time.time()

    if trigger_type == "confidence_collapse":
        # Classic confidence collapse — no clear winner
        return [{
            "state_id": "stable_narrative_v3",
            "hypotheses": {"frame_A": 0.31, "frame_B": 0.29, "frame_C": 0.28},
            "timestamp": now,
        }]

    elif trigger_type == "oscillation":
        # Rapid flip-flopping between two attractors inside the
        # oscillation window — the top hypothesis swaps each observation.
        return [
            {
                "state_id": "decision_paralysis_loop",
                "hypotheses": {"explore": 0.51, "exploit": 0.49}
                if i % 2 == 0
                else {"explore": 0.49, "exploit": 0.51},
                "timestamp": now + i * 0.1,
            }
            for i in range(4)
        ]

    elif trigger_type == "frame_conflict":
        # Two strong but incompatible frames
        return [{
            "state_id": "value_tension_state",
            "hypotheses": {"ethical_priority": 0.67, "efficiency_priority": 0.64},
            "timestamp": now,
        }]

    elif trigger_type == "rapid_switch":
        # Confident context switch — deliberately does NOT trigger LAE.
        # The new context wins decisively, so there is no liminal state
        # to structure. The engine staying dormant here is correct.
        return [{
            "state_id": "model_reconfiguration_pending",
            "hypotheses": {"previous_context": 0.22, "new_context": 0.91},
            "timestamp": now,
        }]

    else:  # default / mixed
        return [{
            "state_id": "ongoing_becoming",
            "hypotheses": {"maintain": 0.38, "adapt": 0.41, "reset": 0.21},
            "timestamp": now,
        }]


def main() -> None:
    print("🌊 Liminal Anchor Engine — Live Demonstration")
    print("   A transition-layer cognitive substrate")
    print("   Built for the moments when the system is no longer what it was.\n")

    engine = LiminalAnchorEngine()
    print("✅ LAE initialized (event-triggered mode, zero external deps)\n")

    # Sequence of transitions that build memory and identity over time
    triggers = [
        "confidence_collapse",
        "oscillation",
        "frame_conflict",
        "rapid_switch",
        "confidence_collapse",  # second collapse — now with memory
    ]

    for i, trigger in enumerate(triggers, 1):
        observations = create_synthetic_observations(trigger, i)
        print(f"\n>>> Feeding observation burst #{i} — trigger: {trigger}")
        print(f"    Source state: {observations[0]['state_id']}")

        result = None
        for obs in observations:
            result = engine.process(obs)

        if result is None:
            print("    → No transition detected. System remains stable.")
            continue

        pretty_print_result(result, i)

        # Small pause for dramatic effect in terminal
        time.sleep(0.4)

    print("\n" + "="*70)
    print("🎉 DEMO COMPLETE")
    print("="*70)
    print("""
LAE successfully:
• Detected multiple distinct transition types
• Mapped ambiguity instead of forcing premature resolution
• Allocated protective anchors while allowing mutation
• Stored rich transition episodes (not just state snapshots)
• Generated directional proto-intents
• Updated a living IdentityGradient across crossings

This is the layer that lets persistent AI selfhood survive turbulence.

Next steps you might explore:
• Wire LAE into your RFE-Core2 loop as a sidecar
• Add custom detectors or field generators
• Build multi-mind merging (Phase 4)
• Expose via the external_api hooks (Phase 5)

Fork it, extend it, make it yours.
The boundary is where the interesting things happen.
""")

    # Optional: dump last result as JSON for further inspection
    if 'result' in locals() and result:
        print("\n📦 Last LiminalResult as JSON (for inspection):")
        # Convert dataclasses to dicts recursively for JSON
        def dc_to_dict(obj):
            if hasattr(obj, '__dataclass_fields__'):
                return {k: dc_to_dict(v) for k, v in asdict(obj).items()}
            if isinstance(obj, list):
                return [dc_to_dict(x) for x in obj]
            if isinstance(obj, dict):
                return {k: dc_to_dict(v) for k, v in obj.items()}
            return obj

        try:
            print(json.dumps(dc_to_dict(result), indent=2, default=str)[:2000] + "...")
        except Exception:
            pass


if __name__ == "__main__":
    main()
