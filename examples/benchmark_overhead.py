"""Runtime-overhead benchmark for the Liminal Anchor Engine.

Measures the cost a host pays to run LAE as a sidecar:

  * init (one-time)
  * per-observation latency when no trigger fires (the common, dormant case)
  * per-observation latency when a transition drives the full pipeline
  * how active latency scales with accumulated memory

Run:  python3 examples/benchmark_overhead.py
"""

from __future__ import annotations

import gc
import statistics
import time

from lae import LAE

DORMANT = {"state_id": "s", "hypotheses": {"a": 0.91, "b": 0.09}}
ACTIVE = {"state_id": "s", "hypotheses": {"a": 0.31, "b": 0.29, "c": 0.28}}


def bench(fn, n=2000, warmup=200):
    for _ in range(warmup):
        fn()
    gc.disable()
    s = []
    for _ in range(n):
        t = time.perf_counter()
        fn()
        s.append(time.perf_counter() - t)
    gc.enable()
    s.sort()
    return {
        "median_us": statistics.median(s) * 1e6,
        "p95_us": s[int(len(s) * 0.95)] * 1e6,
    }


def main():
    t = time.perf_counter()
    _ = LAE()
    print(f"init: {(time.perf_counter() - t) * 1e6:.1f} us")

    dorm = LAE()
    print("dormant (no trigger):  ", bench(lambda: dorm.observe(dict(DORMANT))))

    act = LAE()
    print("active (full pipeline):", bench(lambda: act.observe(dict(ACTIVE))))

    print("\nactive latency vs accumulated activations "
          "(flat past the scan cap):")
    for pf in (0, 100, 500, 1000, 2000):
        e = LAE()
        for _ in range(pf):
            e.observe(dict(ACTIVE))
        s = []
        for _ in range(200):
            t = time.perf_counter()
            e.observe(dict(ACTIVE))
            s.append(time.perf_counter() - t)
        print(f"  after {pf:5d}: {statistics.median(s) * 1e6:8.1f} us")


if __name__ == "__main__":
    main()
