"""
lae.integration.diagnostics — Observability + diagnostics layer (Phase 5).

Read-only introspection over a running engine. Diagnostics NEVER mutate
state — firewalled from the pipeline by construction (RFE discipline:
diagnostics firewalled from CI/runtime).

Provides:
- snapshot(): one-call health summary of an engine
- activation_stats(): trigger counts, dormancy ratio
- memory_stats(): episode counts, compression activity
- identity_stats(): invariant count, rigidity distribution, drift
- collective_stats(): for MultiMindCoordinator
"""

from __future__ import annotations

from typing import Any

from ..pipeline import LiminalAnchorEngine


class Diagnostics:
    def __init__(self, engine: LiminalAnchorEngine) -> None:
        self._engine = engine
        self._observations = 0
        self._activations = 0

    # ------------------------------------------------------------------
    # Counters fed by the API wrapper (read-side only).
    def count_observation(self, activated: bool) -> None:
        self._observations += 1
        if activated:
            self._activations += 1

    # ------------------------------------------------------------------
    def activation_stats(self) -> dict[str, Any]:
        dormancy = (
            1.0 - (self._activations / self._observations)
            if self._observations
            else 1.0
        )
        return {
            "observations": self._observations,
            "activations": self._activations,
            "dormancy_ratio": round(dormancy, 4),
        }

    def memory_stats(self) -> dict[str, Any]:
        mem = self._engine.memory
        episodes = mem.all_episodes()
        compressed = [
            e for e in episodes if "compressed_from" in e.ambiguity_signature
        ]
        return {
            "episode_count": len(mem),
            "compressed_episodes": len(compressed),
            "unique_sources": len({e.source_state_id for e in episodes}),
        }

    def identity_stats(self) -> dict[str, Any]:
        ident = self._engine.identity_mapper.field_model.current
        rigidity_values = list(ident.rigidity.values())
        return {
            "invariant_count": len(ident.invariants),
            "plasticity_zone_count": len(ident.plasticity_zones),
            "trajectory_length": len(ident.trajectory_history),
            "mean_rigidity": round(
                sum(rigidity_values) / len(rigidity_values), 4
            )
            if rigidity_values
            else 0.0,
            "max_rigidity": max(rigidity_values, default=0.0),
            "drift_dimensions": len(ident.drift_vectors),
        }

    # ------------------------------------------------------------------
    def snapshot(self) -> dict[str, Any]:
        """One-call health summary."""
        return {
            "activation": self.activation_stats(),
            "memory": self.memory_stats(),
            "identity": self.identity_stats(),
        }
