#!/usr/bin/env python3
"""
rfe_integration.py — Wiring LAE as a sidecar to an RFE-Core2 loop.

RFE-Core2 (github.com/SamuelJacksonGrim/RFE-Core2) is a recursive field
engine: each AutonomousCycle.step() runs ~22 phases (generate → attractor
pull → watcher evaluation → witness update → emotional gradient →
governance gate ...) and routes behavior by cognitive rhythm — one of
four states: stabilize, dream, reflect, explore.

LAE's job in that architecture is the moments BETWEEN rhythms: when the
rhythm router's pull flattens, watcher coherence drops, and the engine
is no longer clearly in any single mode. That is a liminal state, and it
is exactly the observation contract LAE detects on:

    RFE telemetry (per cycle)              LAE observation
    ---------------------------            ---------------------------
    current routed rhythm          ──────▶ state_id
    rhythm router weights          ──────▶ hypotheses {rhythm: weight}
    subjective time tick           ──────▶ timestamp

The translation lives in RFESidecar below. This script runs against a
small mock of the RFE cycle so it works standalone; the "Wiring it for
real" note at the bottom shows the one-line change for a live engine.

Run from the repo root:
    python examples/rfe_integration.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

# Allow running straight from a repo checkout without pip install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lae import LAE, ObservationOutcome


# ---------------------------------------------------------------------------
# The adapter — this is the part you copy into an RFE-Core2 host.
# ---------------------------------------------------------------------------

class RFESidecar:
    """Feeds RFE-Core2 cycle telemetry into LAE and collects what comes back.

    LAE never steers the loop. ProtoIntent is logged as advisory pressure
    (Contract #5: direction, not decision) — the rhythm router remains
    the only thing that routes.
    """

    def __init__(self) -> None:
        self.lae = LAE()
        self.advisory_log: list[dict[str, Any]] = []

        # Tag every crossing with host context via the annotation hook.
        self.lae.hooks.on_pre_resolution(
            lambda payload: {"host": "rfe-core2", "layer": "rhythm_router"}
        )

    def after_cycle(self, telemetry: dict[str, Any]) -> ObservationOutcome:
        """Call once per AutonomousCycle.step(), after watcher evaluation.

        Expected telemetry keys (all present in the RFE cycle spine):
            cycle: int                       — cycle counter
            rhythm: str                      — currently routed rhythm
            rhythm_weights: dict[str, float] — router pull per rhythm state
            coherence: float                 — watcher composite (unused by
                                               LAE, logged for provenance)
        """
        outcome = self.lae.observe({
            "state_id": f"rhythm::{telemetry['rhythm']}",
            "hypotheses": dict(telemetry["rhythm_weights"]),
            "timestamp": float(telemetry["cycle"]),  # subjective ticks work fine
        })

        if outcome.activated:
            intent = outcome.result.intent
            self.advisory_log.append({
                "cycle": telemetry["cycle"],
                "watcher_coherence": telemetry["coherence"],
                "leaving": outcome.result.event.source_state_id,
                "pressure": intent.vector,          # advisory only
                "pressure_stability": intent.stability_score,
                "anchored": [a.anchor_id for a in outcome.result.anchors],
            })
        return outcome


# ---------------------------------------------------------------------------
# Mock RFE cycle — emulates the telemetry shape of AutonomousCycle.step().
# A stable stretch, a destabilization window (coherence sags, router pull
# flattens, rhythm flip-flops), then resettling into a new rhythm.
# ---------------------------------------------------------------------------

def mock_rfe_run() -> list[dict[str, Any]]:
    def cycle(n: int, rhythm: str, weights: dict[str, float], coherence: float):
        return {"cycle": n, "rhythm": rhythm, "rhythm_weights": weights,
                "coherence": coherence}

    return [
        # Settled: stabilize dominates, coherence high. LAE should sleep.
        cycle(1, "stabilize", {"stabilize": 0.82, "reflect": 0.08,
                               "explore": 0.06, "dream": 0.04}, 0.91),
        cycle(2, "stabilize", {"stabilize": 0.79, "reflect": 0.10,
                               "explore": 0.07, "dream": 0.04}, 0.90),
        # Perturbation lands: router pull flattens (hypothesis conflict).
        cycle(3, "stabilize", {"stabilize": 0.31, "reflect": 0.30,
                               "explore": 0.27, "dream": 0.12}, 0.55),
        # Rhythm flip-flops inside the window (frame oscillation).
        cycle(4, "reflect", {"reflect": 0.40, "explore": 0.38,
                             "stabilize": 0.14, "dream": 0.08}, 0.48),
        cycle(5, "explore", {"explore": 0.41, "reflect": 0.39,
                             "stabilize": 0.12, "dream": 0.08}, 0.46),
        cycle(6, "reflect", {"reflect": 0.40, "explore": 0.39,
                             "stabilize": 0.13, "dream": 0.08}, 0.47),
        # Resettled: explore wins decisively. LAE should go quiet again.
        cycle(7, "explore", {"explore": 0.85, "reflect": 0.07,
                             "stabilize": 0.05, "dream": 0.03}, 0.88),
    ]


def main() -> None:
    print("🔁 LAE × RFE-Core2 — sidecar integration demo\n")
    sidecar = RFESidecar()

    for telemetry in mock_rfe_run():
        outcome = sidecar.after_cycle(telemetry)
        status = "LIMINAL — crossing structured" if outcome.activated else "settled"
        print(f"  cycle {telemetry['cycle']}: rhythm={telemetry['rhythm']:<9} "
              f"coherence={telemetry['coherence']:.2f}  → {status}")

    print(f"\n  Crossings structured: {len(sidecar.advisory_log)}")
    for entry in sidecar.advisory_log:
        top = max(entry["pressure"], key=entry["pressure"].get) if entry["pressure"] else "—"
        print(f"    cycle {entry['cycle']}: leaving {entry['leaving']}, "
              f"lean → {top} (stability {entry['pressure_stability']:.1f}, "
              f"{len(entry['anchored'])} anchors)")

    identity = sidecar.lae.diagnostics.snapshot()["identity"]
    print(f"\n  Identity across the run: {identity['trajectory_length']} trajectory "
          f"points, {identity['plasticity_zone_count']} plastic zones, "
          f"{identity['invariant_count']} invariants")

    print("""
Wiring it for real
------------------
In RFE-Core2, instantiate one RFESidecar next to the engine and call it
at the end of AutonomousCycle.step(), after watcher evaluation — the
point where rhythm weights and coherence are both fresh:

    sidecar = RFESidecar()
    ...
    telemetry = {"cycle": self.tick, "rhythm": self.rhythm,
                 "rhythm_weights": self.rhythm_router.weights(),
                 "coherence": watcher_report.composite}
    sidecar.after_cycle(telemetry)

The advisory_log is yours to surface (e.g. into the topological_log or
the witness). Per Contract #5, never route on the intent vector directly
— it is pressure, not a decision.
""")


if __name__ == "__main__":
    main()
