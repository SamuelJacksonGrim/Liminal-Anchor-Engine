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
    python demo.py

Or with the package installed:
    python -m lae_demo.demo

Zero extra dependencies beyond what's in LAE itself.
"""

from __future__ import annotations

import json
import time
from dataclasses import asdict
from typing import Any

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
    print(f"   Time Window      : {event.time_window.duration():.1f}ms")

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


def create_synthetic_observation(trigger_type: str, step: int) -> dict[str, Any]:
    """
    Create realistic synthetic observations that trigger different LAE conditions.
    These mimic what a host cognitive system might emit.
    """
    base = {
        "timestamp": time.time(),
        "step": step,
        "context_id": f"ctx_{step:03d}",
    }

    if trigger_type == "confidence_collapse":
        # Classic confidence collapse — no clear winner
        return {
            **base,
            "hypotheses": ["frame_A", "frame_B", "frame_C"],
            "confidences": {"frame_A": 0.31, "frame_B": 0.29, "frame_C": 0.28},
            "conflict_score": 0.82,
            "oscillation_count": 0,
            "trigger": "confidence_collapse",
            "source_state": "stable_narrative_v3",
        }

    elif trigger_type == "oscillation":
        # Rapid flip-flopping between two attractors
        return {
            **base,
            "hypotheses": ["explore", "exploit"],
            "confidences": {"explore": 0.51, "exploit": 0.49},
            "conflict_score": 0.71,
            "oscillation_count": 4,
            "oscillation_window_ms": 1200,
            "trigger": "frame_oscillation",
            "source_state": "decision_paralysis_loop",
        }

    elif trigger_type == "frame_conflict":
        # Two strong but incompatible frames
        return {
            **base,
            "hypotheses": ["ethical_priority", "efficiency_priority"],
            "confidences": {"ethical_priority": 0.67, "efficiency_priority": 0.64},
            "conflict_score": 0.89,
            "semantic_distance": 0.78,
            "trigger": "hypothesis_conflict",
            "source_state": "value_tension_state",
        }

    elif trigger_type == "rapid_switch":
        # Sudden context/model change
        return {
            **base,
            "hypotheses": ["previous_context", "new_context"],
            "confidences": {"previous_context": 0.22, "new_context": 0.91},
            "conflict_score": 0.55,
            "context_switch_velocity": "high",
            "trigger": "rapid_context_switch",
            "source_state": "model_reconfiguration_pending",
        }

    else:  # default / mixed
        return {
            **base,
            "hypotheses": ["maintain", "adapt", "reset"],
            "confidences": {"maintain": 0.38, "adapt": 0.41, "reset": 0.21},
            "conflict_score": 0.65,
            "trigger": "mixed_instability",
            "source_state": "ongoing_becoming",
        }


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
        obs = create_synthetic_observation(trigger, i)
        print(f"\n>>> Feeding observation #{i} — trigger: {trigger}")
        print(f"    Source state hint: {obs.get('source_state', 'unknown')}")

        result = engine.process(obs)

        if result is None:
            print("   → No transition detected. System remains stable.")
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
