"""
lae.intent.proto_intent_synthesizer — Proto-intent heuristic generator (Phase 1).

Layer 5. Input: LiminalMemoryEpisode(s) + current AmbiguityField.
Output: ProtoIntent.

Contract #5: proto-intent is directional only. It binds no decision.
It is the pre-decisional "lean" of the system while still inside the
liminal space — direction without commitment.

Phase 1 heuristic:
- vector: per-candidate pull combining current field gradients with
  historical pull from similar past episodes (if any).
- magnitude: L2 norm of the vector — how strongly the system leans
  at all, regardless of where.
- stability_score: agreement between current gradients and history.
  High = the lean is temporally coherent. Low = the lean is novel or
  contradicts past crossings. NOTE: reflects coherence, not
  correctness (per contract).
"""

from __future__ import annotations

import math

from ..config import LAEConfig
from ..types import AmbiguityField, LiminalMemoryEpisode, ProtoIntent


class ProtoIntentSynthesizer:
    HISTORY_WEIGHT = 0.35  # how much past crossings pull on the present

    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()

    def synthesize(
        self,
        field: AmbiguityField,
        similar_episodes: list[LiminalMemoryEpisode] | None = None,
    ) -> ProtoIntent:
        similar_episodes = similar_episodes or []

        # Current pull straight from the field gradients.
        vector: dict[str, float] = dict(field.gradients)

        # Historical pull: candidates that appear as leading targets in
        # similar past episodes get reinforced.
        history_pull: dict[str, float] = {}
        for ep in similar_episodes:
            if ep.target_state_ids:
                leading = f"region::{ep.target_state_ids[0]}"
                history_pull[leading] = history_pull.get(leading, 0.0) + 1.0

        if history_pull:
            max_pull = max(history_pull.values())
            for rid, pull in history_pull.items():
                boost = (pull / max_pull) * self.HISTORY_WEIGHT
                vector[rid] = round(vector.get(rid, 0.0) + boost, 4)

        magnitude = round(math.sqrt(sum(v * v for v in vector.values())), 4)

        stability = self._stability(field, history_pull)

        return ProtoIntent(
            vector=vector,
            magnitude=magnitude,
            stability_score=stability,
            origin_episode_ids=[ep.episode_id for ep in similar_episodes],
            ambiguity_lineage=[r.id for r in field.regions],
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _stability(field: AmbiguityField, history_pull: dict[str, float]) -> float:
        """Agreement between present gradients and historical pull.

        No history -> neutral 0.5 (novel territory, neither stable nor
        unstable). Otherwise: does history point where the field
        already leans?
        """
        if not history_pull or not field.gradients:
            return 0.5
        field_top = max(field.gradients, key=field.gradients.get)
        history_top = max(history_pull, key=history_pull.get)
        if field_top == history_top:
            return 0.9
        # History exists but disagrees — the lean is contested in time.
        return 0.2
