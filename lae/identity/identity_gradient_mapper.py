"""
lae.identity.identity_gradient_mapper — Layer 6: IdentityGradientMapper (Phase 3).

Input: LiminalMemoryEpisode + current AmbiguityField + Anchor set.
Output: identity_shift_delta (applied to IdentityFieldModel).

Responsibilities:
1. Feed episode data to InvarianceTracker and PlasticityAnalyzer.
2. Ask EvolutionDynamics for current drift vectors.
3. Compute the identity_shift_delta for this episode.
4. Apply the delta to the live IdentityFieldModel.
5. Return both the delta and the updated IdentityGradient snapshot.

The mapper never selects a resolution. It maps what happened to
identity — the direction the field moved, which features hardened,
which zones became more plastic — without deciding what comes next.
That is still the intent layer's job.
"""

from __future__ import annotations

from typing import Any

from ..config import LAEConfig
from ..types import AmbiguityField, Anchor, IdentityGradient, LiminalMemoryEpisode
from .evolution_dynamics import EvolutionDynamics
from .identity_field_model import IdentityFieldModel
from .invariance_tracker import InvarianceTracker
from .plasticity_analyzer import PlasticityAnalyzer


class IdentityGradientMapper:
    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()
        self.field_model = IdentityFieldModel(config)
        self.invariance_tracker = InvarianceTracker()
        self.plasticity_analyzer = PlasticityAnalyzer()
        self.evolution_dynamics = EvolutionDynamics()
        self._step = 0

    # ------------------------------------------------------------------
    def map(
        self,
        episode: LiminalMemoryEpisode,
        field: AmbiguityField,
        anchors: list[Anchor],
    ) -> tuple[dict[str, Any], IdentityGradient]:
        """Compute identity_shift_delta and update the live field model.

        Returns:
            (identity_shift_delta, current IdentityGradient snapshot)
        """
        self._step += 1

        # Enrich the episode signature with anchor data for trackers.
        enriched_sig = dict(episode.ambiguity_signature)
        all_protected = [f for a in anchors for f in a.protected_features]
        all_allowed = [f for a in anchors for f in a.allowed_mutations]
        enriched_sig["protected_features"] = all_protected
        enriched_sig["allowed_mutations_seen"] = all_allowed

        # Feed trackers.
        enriched_episode = LiminalMemoryEpisode(
            episode_id=episode.episode_id,
            source_state_id=episode.source_state_id,
            target_state_ids=episode.target_state_ids,
            anchors_used=episode.anchors_used,
            ambiguity_signature=enriched_sig,
            identity_shift_delta=episode.identity_shift_delta,
        )
        self.invariance_tracker.observe(enriched_episode)
        self.plasticity_analyzer.observe(enriched_episode)

        # Derive direction from field gradients.
        direction = dict(field.gradients)

        # Evolution dynamics.
        evolution = self.evolution_dynamics.update(direction, self._step)

        # Rigidity updates from plasticity analyzer.
        rigidity_map = self.plasticity_analyzer.rigidity_map()

        # New invariant candidates.
        new_invariants = self.invariance_tracker.invariant_candidates()

        # Plasticity zones from analyzer.
        plastic_zones = self.plasticity_analyzer.plasticity_zones()

        # Build the delta.
        delta: dict[str, Any] = {
            "direction_updates": direction,
            "rigidity_updates": {
                k: v - self.field_model.current.rigidity.get(k, 0.0)
                for k, v in rigidity_map.items()
            },
            "new_invariants": new_invariants,
            "new_plasticity_zones": plastic_zones,
            "drift_updates": evolution["drift_vectors"],
            "snapshot": {
                "step": self._step,
                "episode_id": episode.episode_id,
                "source_state_id": episode.source_state_id,
                "drift_magnitude": evolution["drift_magnitude"],
                "oscillating": evolution["oscillating"],
                "region_count": len(field.regions),
            },
        }

        # Apply delta to the live model.
        self.field_model.apply_delta(delta)

        return delta, self.field_model.current
