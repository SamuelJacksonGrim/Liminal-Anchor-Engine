"""
lae.identity.identity_field_model — Live IdentityGradient state (Phase 3).

This is the system's running self-model: identity as a gradient field,
not a vector. It holds the current IdentityGradient and exposes
controlled mutation. Contract #6 is enforced at every write:

- invariants are append-only (features can become invariant but
  cannot be un-invarianted once established)
- trajectory_history is strictly append-only
- rigidity values are clamped [0, 1]
- plasticity_zones are updated, never cleared entirely

Safety flag: prevent_identity_crystallization — if ALL features would
become rigid (rigidity >= 0.9), the lowest-rigidity non-invariant
feature is held back to preserve a plasticity zone. The system cannot
fully freeze.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from ..config import LAEConfig
from ..types import IdentityGradient

RIGIDITY_MIN = 0.0
RIGIDITY_MAX = 1.0
CRYSTALLIZATION_CEILING = 0.9   # no feature may exceed this if it would cause full freeze


class IdentityFieldModel:
    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()
        self._state = IdentityGradient(
            invariants=[],
            direction={},
            rigidity={},
            plasticity_zones=[],
            drift_vectors={},
            trajectory_history=[],
        )

    # ------------------------------------------------------------------
    @property
    def current(self) -> IdentityGradient:
        return self._state

    # ------------------------------------------------------------------
    def apply_delta(self, delta: dict[str, Any]) -> None:
        """Incrementally update the identity field from an episode's delta.

        Delta keys (all optional):
            direction_updates: dict[str, float]
            rigidity_updates: dict[str, float]  (additive)
            new_invariants: list[str]
            new_plasticity_zones: list[str]
            drift_updates: dict[str, float]
            snapshot: dict  (appended to trajectory_history)
        """
        s = self._state

        if "direction_updates" in delta:
            for k, v in delta["direction_updates"].items():
                s.direction[k] = round(v, 4)

        if "rigidity_updates" in delta:
            for k, v in delta["rigidity_updates"].items():
                current = s.rigidity.get(k, 0.0)
                s.rigidity[k] = round(
                    max(RIGIDITY_MIN, min(RIGIDITY_MAX, current + v)), 4
                )

        if "new_invariants" in delta:
            for feat in delta["new_invariants"]:
                if feat not in s.invariants:
                    s.invariants.append(feat)

        if "new_plasticity_zones" in delta:
            for zone in delta["new_plasticity_zones"]:
                if zone not in s.plasticity_zones:
                    s.plasticity_zones.append(zone)

        if "drift_updates" in delta:
            for k, v in delta["drift_updates"].items():
                s.drift_vectors[k] = round(v, 4)

        if "snapshot" in delta:
            s.trajectory_history.append(delta["snapshot"])

        if self.config.prevent_identity_crystallization:
            self._enforce_plasticity()

    # ------------------------------------------------------------------
    def export_state(self) -> dict[str, Any]:
        return dataclasses.asdict(self._state)

    def restore_state(self, state: dict[str, Any]) -> None:
        self._state = IdentityGradient(**state)

    # ------------------------------------------------------------------
    def _enforce_plasticity(self) -> None:
        """Ensure at least one non-invariant feature stays below the
        crystallization ceiling."""
        s = self._state
        non_invariant = {k: v for k, v in s.rigidity.items() if k not in s.invariants}
        if not non_invariant:
            return
        if all(v >= CRYSTALLIZATION_CEILING for v in non_invariant.values()):
            # Release the least-rigid non-invariant feature.
            softest = min(non_invariant, key=non_invariant.get)
            s.rigidity[softest] = round(CRYSTALLIZATION_CEILING - 0.1, 4)
            if softest not in s.plasticity_zones:
                s.plasticity_zones.append(softest)
