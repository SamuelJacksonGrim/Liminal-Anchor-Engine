"""
lae.identity.evolution_dynamics — Identity field evolution analysis (Phase 3).

Computes:
- drift_vectors: how fast and in what direction the identity gradient
  is changing between transitions (velocity of the field, not position)
- oscillation_detected: whether the field is cycling between the same
  attractors without settling
- trajectory_snapshot: a point-in-time snapshot to append to
  trajectory_history

Drift is computed as the delta between the current direction and the
exponential moving average of past directions. A high drift magnitude
means the identity field is moving fast. Near-zero drift means it is
settling or has settled.
"""

from __future__ import annotations

import math
from typing import Any

EMA_ALPHA = 0.3              # exponential moving average weight for current
OSCILLATION_WINDOW = 6       # look back this many snapshots for oscillation
OSCILLATION_FLIP_THRESHOLD = 3  # >= this many direction reversals = oscillating


class EvolutionDynamics:
    def __init__(self) -> None:
        self._direction_ema: dict[str, float] = {}
        self._snapshot_history: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    def update(
        self,
        current_direction: dict[str, float],
        step: int,
    ) -> dict[str, Any]:
        """Compute evolution metrics for the current step.

        Returns a dict with:
            drift_vectors, drift_magnitude, oscillating, snapshot
        """
        # Update EMA
        for k, v in current_direction.items():
            prev = self._direction_ema.get(k, v)
            self._direction_ema[k] = round(EMA_ALPHA * v + (1 - EMA_ALPHA) * prev, 4)

        # Drift = current - EMA
        drift: dict[str, float] = {
            k: round(current_direction.get(k, 0.0) - self._direction_ema.get(k, 0.0), 4)
            for k in set(current_direction) | set(self._direction_ema)
        }
        drift_magnitude = round(math.sqrt(sum(v * v for v in drift.values())), 4)

        oscillating = self._check_oscillation(current_direction)

        snapshot = {
            "step": step,
            "direction": dict(current_direction),
            "drift_magnitude": drift_magnitude,
            "oscillating": oscillating,
        }
        self._snapshot_history.append(snapshot)

        return {
            "drift_vectors": drift,
            "drift_magnitude": drift_magnitude,
            "oscillating": oscillating,
            "snapshot": snapshot,
        }

    # ------------------------------------------------------------------
    def _check_oscillation(self, current: dict[str, float]) -> bool:
        """Count direction reversals in recent history."""
        recent = self._snapshot_history[-OSCILLATION_WINDOW:]
        if len(recent) < 3:
            return False

        # Find the dominant dimension per snapshot.
        def dominant(d: dict[str, float]) -> str | None:
            if not d:
                return None
            return max(d, key=d.get)

        tops = [dominant(s["direction"]) for s in recent] + [dominant(current)]
        flips = sum(1 for a, b in zip(tops, tops[1:]) if a != b and a and b)
        return flips >= OSCILLATION_FLIP_THRESHOLD
