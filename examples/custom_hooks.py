#!/usr/bin/env python3
"""
custom_hooks.py — Phase 5: participating in the pipeline from the host side.

Shows the three hook seams plus the event stream:

- pre_transition: veto noise before LAE spends effort on it
- pre_resolution: annotate the result (but never mutate the intent)
- reconfiguration: inject a host-side model_reconfiguration signal
- events.subscribe: tap the per-activation event stream

Run from the repo root:
    python examples/custom_hooks.py
"""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running straight from a repo checkout without pip install.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lae import LAE


def main() -> None:
    print("🪝 LAE Hooks Demonstration (Phase 5)\n")

    engine = LAE()

    # --- Event stream tap -----------------------------------------------
    stream: list[str] = []
    for topic in ["transition.detected", "intent.synthesized", "safety.triggered"]:
        engine.events.subscribe(topic, lambda payload, t=topic: stream.append(t))

    # --- Hook 1: veto transitions the host knows are noise ---------------
    def ignore_sensor_glitches(observation: dict) -> bool:
        if observation.get("source") == "flaky_sensor":
            print("    [pre_transition] vetoed: flaky_sensor noise")
            return False
        return True

    engine.hooks.on_pre_transition(ignore_sensor_glitches)

    # --- Hook 2: annotate the result without touching the intent ---------
    def attach_host_context(payload: dict) -> dict:
        return {"host_mood": "curious", "top_anchor": payload["anchors"][0].anchor_id}

    engine.hooks.on_pre_resolution(attach_host_context)

    unstable = {
        "state_id": "belief_v2",
        "hypotheses": {"revise": 0.34, "hold": 0.33, "discard": 0.28},
    }

    print(">>> Observation from a flaky sensor (host vetoes it)")
    out = engine.observe({**unstable, "source": "flaky_sensor"})
    print(f"    activated={out.activated} vetoed={out.vetoed}\n")

    print(">>> Same instability from a trusted source")
    out = engine.observe({**unstable, "source": "trusted"})
    print(f"    activated={out.activated}")
    print(f"    host_annotations: {out.host_annotations}\n")

    print(">>> Host-injected model reconfiguration signal")
    engine.reconfigure({"reason": "weights_swapped", "model": "v2 -> v3"})

    print(f"\n    event stream seen by host: {stream}")
    print(f"    diagnostics: {engine.diagnostics.snapshot()['activation']}")

    print("\n🎉 Hooks demo complete — the host participated without touching internals.")


if __name__ == "__main__":
    main()
