# LAE runtime overhead

Cost of running the Liminal Anchor Engine as a sidecar, measured with
`examples/benchmark_overhead.py` (pure Python, no deps; absolute numbers are
machine-dependent — the *scaling shape* is the point).

## One-time
- Cold import: ~24 ms
- Engine init: ~90 µs

## Per `observe()` call
| Case | Cost |
|---|---|
| Confident switch — no trigger (dormant) | ~140 µs |
| Transition fires → full pipeline | ~155 µs first, then bounded (see below) |

A confident, non-liminal observation fires nothing — the engine staying
dormant outside liminal states is by design — so most host cycles pay only
the ~140 µs detector floor.

## Scaling — bounded similarity retrieval

The active path retrieves structurally similar past episodes. That scan used
to compare against **every** stored episode, so per-activation cost climbed
with memory:

| Prior activations | latency (before → after) |
|---|---|
| 0    | 690 µs → 670 µs |
| 1000 | 6.2 ms → ~2.5 ms |
| 2000 | (still climbing) → ~2.5 ms (flat) |

`AmbiguitySignatureIndex` now caps the scan to the most-recent
`memory.retrieval_scan_limit` episodes (default **512**; `0` disables the cap).
Stores smaller than the cap are unaffected, so existing behavior is unchanged
until memory actually grows large. Covered by
`tests/unit/test_retrieval_scan_limit.py`.

## Notes / further knobs
- Memory itself is append-only by design (Contract #1: transitions are stored
  as first-class history). The scan cap bounds retrieval *cost*, not retained
  size; compression (`memory.compression`) is the lever for retained size.
- The ~140 µs dormant floor is detector bookkeeping (history append +
  oscillation-window scan) run on every observation. It is already small; an
  early-out for confidently-dominant observations could trim it further but
  was left out to avoid touching detector trigger semantics.
