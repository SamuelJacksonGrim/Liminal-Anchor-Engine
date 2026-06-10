"""
tests.smoke.synthetic_transition — Phase 1 end-to-end smoke test.

Diagnostic-script form (run with: python -m tests.smoke.synthetic_transition).

Drives the full pipeline with synthetic observations covering all three
Phase 1 trigger rules, then verifies the Phase 1 outcome criterion from
the README: "System can run synthetic transitions end-to-end."

Pre-declared signatures:
  SUCCESS: all 7 checks pass; dormant observations produce None;
           triggered observations produce complete LiminalResult objects;
           memory accumulates; second similar transition retrieves the first.
  FAILURE: any check raises or mismatches — printed with FAIL marker,
           exit code 1.
"""

from __future__ import annotations

import sys

from lae.pipeline import LiminalAnchorEngine

PASS = "✅ PASS"
FAIL = "❌ FAIL"

results: list[bool] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    marker = PASS if condition else FAIL
    print(f"  {marker}  {name}" + (f" — {detail}" if detail else ""))
    results.append(condition)


def main() -> int:
    print("=" * 64)
    print("LAE Phase 1 smoke test — synthetic transitions end-to-end")
    print("=" * 64)

    engine = LiminalAnchorEngine()

    # ------------------------------------------------------------------
    print("\n[1] Dormancy: confident, unambiguous observation")
    result = engine.process(
        {
            "state_id": "state::working",
            "hypotheses": {"state::working_continue": 0.92},
            "timestamp": 1000.0,
        }
    )
    check("no trigger -> pipeline returns None", result is None)

    # ------------------------------------------------------------------
    print("\n[2] Trigger: confidence_collapse (all hypotheses weak)")
    result = engine.process(
        {
            "state_id": "state::working",
            "hypotheses": {
                "state::rest": 0.30,
                "state::explore": 0.25,
                "state::defend": 0.20,
            },
            "timestamp": 1001.0,
        }
    )
    check("collapse produces LiminalResult", result is not None)
    if result:
        check(
            "TransitionEvent carries source + candidates",
            result.event.source_state_id == "state::working"
            and len(result.event.candidate_target_states) == 3,
        )
        check(
            "AmbiguityField has >= min_regions regions",
            len(result.field.regions) >= engine.config.min_regions,
            f"{len(result.field.regions)} regions",
        )
        check(
            "conflict topology populated (contested candidates)",
            len(result.field.conflict_topology) > 0,
            f"{sum(len(v) for v in result.field.conflict_topology.values()) // 2} edges",
        )
        check(
            "anchors allocated within cap",
            0 < len(result.anchors) <= engine.config.max_active_anchors,
            f"{len(result.anchors)} anchors",
        )
        continuity = [a for a in result.anchors if "continuity" in a.anchor_id]
        check("continuity anchor on source boundary", len(continuity) == 1)
        check(
            "episode stored, signature indexed",
            len(engine.memory) == 1
            and result.episode.ambiguity_signature["region_count"]
            == len(result.field.regions),
        )
        check(
            "proto-intent is directional with magnitude > 0",
            result.intent.magnitude > 0 and len(result.intent.vector) > 0,
            f"magnitude={result.intent.magnitude}",
        )
        check(
            "no history -> neutral stability 0.5",
            result.intent.stability_score == 0.5,
        )

    # ------------------------------------------------------------------
    print("\n[3] Memory: similar transition retrieves precedent")
    result2 = engine.process(
        {
            "state_id": "state::working",
            "hypotheses": {
                "state::rest": 0.31,
                "state::explore": 0.24,
                "state::defend": 0.21,
            },
            "timestamp": 1002.0,
        }
    )
    check("second similar transition triggers", result2 is not None)
    if result2:
        check(
            "precedent episode retrieved into intent lineage",
            len(result2.intent.origin_episode_ids) == 1,
            f"origins={result2.intent.origin_episode_ids}",
        )
        check(
            "history agreement raises stability",
            result2.intent.stability_score > 0.5,
            f"stability={result2.intent.stability_score}",
        )
        check("memory accumulates", len(engine.memory) == 2)

    # ------------------------------------------------------------------
    print("\n[4] Trigger: frame_oscillation (top hypothesis flip-flops)")
    osc_engine = LiminalAnchorEngine()
    t = 2000.0
    osc_results = []
    for top in ["state::a", "state::b", "state::a", "state::b"]:
        other = "state::b" if top == "state::a" else "state::a"
        osc_results.append(
            osc_engine.process(
                {
                    "state_id": "state::unstable",
                    "hypotheses": {top: 0.85, other: 0.10},
                    "timestamp": t,
                }
            )
        )
        t += 0.3
    check(
        "oscillation detected within window",
        any(
            r is not None
            and "state::unstable" == r.event.source_state_id
            for r in osc_results
        ),
    )

    # ------------------------------------------------------------------
    print("\n[5] Contract spot-checks")
    if result:
        check(
            "Contract #4: episode stores crossing, not state snapshots",
            "state_snapshot" not in result.episode.__dict__
            and result.episode.identity_shift_delta == {},
        )
        check(
            "Contract #5: intent binds no decision (vector only)",
            not hasattr(result.intent, "decision")
            and not hasattr(result.intent, "selected_target"),
        )
        check(
            "Contract #2: field maps ambiguity (voids/islands present as lists)",
            isinstance(result.field.voids, list)
            and isinstance(result.field.coherence_islands, list),
        )

    # ------------------------------------------------------------------
    passed = sum(results)
    total = len(results)
    print("\n" + "=" * 64)
    print(f"RESULT: {passed}/{total} checks passed")
    print("=" * 64)
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
