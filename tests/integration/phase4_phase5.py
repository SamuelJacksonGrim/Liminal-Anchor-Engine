"""
tests.integration.phase4_phase5 — Integration test for Phase 4 & 5.

Run with: python -m tests.integration.phase4_phase5

Pre-declared signatures:
  SUCCESS:
    Phase 4 —
    - per-agent pipelines stay isolated (separate memory/identity)
    - merged event preserves dissent, raises collective conflict on
      cross-agent divergence
    - shared field keeps minority regions, adds cross-agent conflict edges
    - opposing intents partially cancel (collective magnitude drops)
    - aligned intents don't cancel (alignment preserves stability)
    Phase 5 —
    - event stream emits all 6 per-activation event types in order
    - subscriber exceptions are isolated
    - pre_transition veto blocks processing
    - pre_resolution annotations ride alongside, intent untouched
    - reconfigure() emits safety event
    - diagnostics reflect activity, never mutate
    - regression: Phase 1 smoke + Phase 2/3 integration still pass
  FAILURE: any check raises or mismatches — exit code 1.
"""

from __future__ import annotations

import sys

from lae.integration.external_api import LAE

PASS = "✅ PASS"
FAIL = "❌ FAIL"
results: list[bool] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    marker = PASS if condition else FAIL
    print(f"  {marker}  {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)


def obs(state: str, hyps: dict, ts: float) -> dict:
    return {"state_id": state, "hypotheses": hyps, "timestamp": ts}


def main() -> int:
    print("=" * 64)
    print("LAE Phase 4 & 5 integration test")
    print("=" * 64)

    # ==================================================================
    print("\n[1] Phase 4 — Agents stay isolated")
    lae = LAE(agents=["claude", "gpt", "gemini"])
    r = lae.observe_collective({
        "claude": obs("state::shared", {"state::a": 0.30, "state::b": 0.28, "state::c": 0.22}, 1000.0),
        "gpt":    obs("state::shared", {"state::a": 0.31, "state::b": 0.27, "state::c": 0.21}, 1000.0),
    })
    check("two agents triggered", r is not None and len(r.agent_results) == 2)
    if r:
        mem_claude = len(lae.coordinator.engines["claude"].memory)
        mem_gemini = len(lae.coordinator.engines["gemini"].memory)
        check("non-participating agent memory untouched",
              mem_claude == 1 and mem_gemini == 0,
              f"claude={mem_claude} gemini={mem_gemini}")

    # ==================================================================
    print("\n[2] Phase 4 — Merged event preserves dissent + raises conflict")
    lae2 = LAE(agents=["a1", "a2"])
    r2 = lae2.observe_collective({
        # a1 and a2 disagree about the source state AND lean opposite ways.
        "a1": obs("state::working", {"state::rest": 0.35, "state::explore": 0.30}, 2000.0),
        "a2": obs("state::drifting", {"state::explore": 0.36, "state::rest": 0.31}, 2000.0),
    })
    check("collective activation with disagreement", r2 is not None and r2.is_collective)
    if r2 and r2.merged_event:
        me = r2.merged_event
        dissent_keys = [k for k in me.confidence_profile if k.startswith("source_dissent")]
        check("source dissent preserved in merged profile",
              len(dissent_keys) == 1, f"keys={dissent_keys}")
        solo_conflict = r2.agent_results["a1"].event.conflict_score
        check("cross-agent divergence raises collective conflict",
              me.conflict_score >= solo_conflict,
              f"collective={me.conflict_score} solo={solo_conflict}")

    # ==================================================================
    print("\n[3] Phase 4 — Shared field keeps every mind's view")
    if r2 and r2.shared_field:
        sf = r2.shared_field
        minority = [reg for reg in sf.regions if "minority_region" in reg.semantic_tags]
        check("minority regions preserved", len(minority) >= 1,
              f"{len(minority)} minority regions")
        seen_tags = [t for reg in sf.regions for t in reg.semantic_tags if t.startswith("seen_by::")]
        check("provenance tags present", len(seen_tags) > 0)
        cross_edges = sum(len(v) for v in sf.conflict_topology.values())
        check("cross-agent conflict edges exist", cross_edges > 0,
              f"{cross_edges} directed edges")

    # ==================================================================
    print("\n[4] Phase 4 — Opposing intents partially cancel")
    if r2 and r2.collective_intent:
        ci = r2.collective_intent
        solo_mags = [res.intent.magnitude for res in r2.agent_results.values()]
        check("collective magnitude <= max solo magnitude (cancellation)",
              ci.magnitude <= max(solo_mags) + 1e-9,
              f"collective={ci.magnitude} solos={solo_mags}")
        solo_stabs = [res.intent.stability_score for res in r2.agent_results.values()]
        check("disagreement lowers collective stability",
              ci.stability_score <= max(solo_stabs),
              f"collective={ci.stability_score}")

    # Aligned agents: no cancellation.
    lae3 = LAE(agents=["b1", "b2"])
    r3 = lae3.observe_collective({
        "b1": obs("state::working", {"state::rest": 0.35, "state::explore": 0.25}, 3000.0),
        "b2": obs("state::working", {"state::rest": 0.34, "state::explore": 0.26}, 3000.0),
    })
    if r3 and r3.collective_intent:
        check("aligned agents: collective stability not collapsed",
              r3.collective_intent.stability_score >= 0.4,
              f"stability={r3.collective_intent.stability_score}")

    # ==================================================================
    print("\n[5] Phase 5 — Event stream")
    lae4 = LAE()
    received: list[str] = []
    lae4.events.subscribe("*", lambda e: received.append(e["type"]))

    def bad_subscriber(e):
        raise RuntimeError("subscriber bug")
    lae4.events.subscribe("intent.synthesized", bad_subscriber)

    out = lae4.observe(obs("state::w", {"state::x": 0.30, "state::y": 0.28, "state::z": 0.22}, 4000.0))
    expected_order = [
        "transition.detected", "field.generated", "anchors.allocated",
        "episode.recorded", "intent.synthesized", "identity.updated",
    ]
    check("all 6 activation events emitted in order",
          received == expected_order, f"got={received}")
    check("subscriber exception isolated",
          out.activated and lae4.events.delivery_failures == 1,
          f"failures={lae4.events.delivery_failures}")

    # ==================================================================
    print("\n[6] Phase 5 — Hooks")
    lae5 = LAE()
    lae5.hooks.on_pre_transition(lambda o: False)  # veto everything
    out5 = lae5.observe(obs("state::w", {"state::x": 0.30, "state::y": 0.28}, 5000.0))
    check("pre_transition veto blocks processing",
          out5.vetoed and not out5.activated and len(lae5._engine.memory) == 0)

    lae6 = LAE()
    lae6.hooks.on_pre_resolution(lambda p: {"host_tag": "annotated"})
    out6 = lae6.observe(obs("state::w", {"state::x": 0.30, "state::y": 0.28, "state::z": 0.22}, 6000.0))
    check("pre_resolution annotations collected",
          out6.activated and out6.host_annotations.get("host_tag") == "annotated")
    if out6.result:
        check("intent untouched by hooks (Contract #5)",
              not hasattr(out6.result.intent, "host_tag"))

    # ==================================================================
    print("\n[7] Phase 5 — Reconfiguration + diagnostics")
    lae7 = LAE()
    recon_events = []
    lae7.events.subscribe("safety.triggered", lambda e: recon_events.append(e))
    lae7.hooks.on_reconfiguration(lambda s: None)
    lae7.reconfigure({"reason": "host model swap"})
    check("reconfigure emits safety event",
          len(recon_events) == 1 and recon_events[0]["payload"]["kind"] == "model_reconfiguration")

    lae8 = LAE()
    lae8.observe(obs("state::calm", {"state::next": 0.95}, 7000.0))      # dormant
    lae8.observe(obs("state::w", {"state::x": 0.30, "state::y": 0.28, "state::z": 0.22}, 7001.0))  # active
    snap = lae8.diagnostics.snapshot()
    check("diagnostics: observations counted",
          snap["activation"]["observations"] == 2
          and snap["activation"]["activations"] == 1,
          f"dormancy={snap['activation']['dormancy_ratio']}")
    check("diagnostics: memory + identity visible",
          snap["memory"]["episode_count"] == 1
          and snap["identity"]["trajectory_length"] == 1)

    # ==================================================================
    print("\n[8] Regression — earlier phases still pass")
    import subprocess
    for mod, label in [
        ("tests.smoke.synthetic_transition", "Phase 1 smoke"),
        ("tests.integration.phase2_phase3", "Phase 2/3 integration"),
    ]:
        proc = subprocess.run([sys.executable, "-m", mod], capture_output=True, text=True)
        check(f"{label} passes", proc.returncode == 0)

    # ==================================================================
    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 64)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 64)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
