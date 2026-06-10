"""
lae.memory.liminal_memory_buffer — In-memory episodic buffer (Phase 1).

Layer 4. Input: AmbiguityField + Anchor set (+ originating
TransitionEvent). Output: LiminalMemoryEpisode, stored and indexed.

Contract #4: memory stores *crossings*, not snapshots. An episode
encodes the shape of a transition — its ambiguity structure, the
anchors applied, and the identity drift it produced — never the full
states on either side.

Phase 1 indexing: ambiguity_signature is a compact structural summary
(region count, void count, island count, mean conflict density,
dominant gradient direction). Episodes are indexed by a hashable key
derived from that signature, enabling Phase 2 similarity retrieval to
slot in without changing the storage layer.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Any

from ..config import LAEConfig
from ..types import AmbiguityField, Anchor, LiminalMemoryEpisode, TransitionEvent

_episode_counter = itertools.count(1)


class LiminalMemoryBuffer:
    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()
        self._episodes: list[LiminalMemoryEpisode] = []
        self._index: dict[str, list[str]] = defaultdict(list)  # sig_key -> episode_ids

    # ------------------------------------------------------------------
    def record(
        self,
        event: TransitionEvent,
        field: AmbiguityField,
        anchors: list[Anchor],
        identity_shift_delta: dict[str, Any] | None = None,
    ) -> LiminalMemoryEpisode:
        signature = self.compute_signature(field)
        episode = LiminalMemoryEpisode(
            episode_id=f"episode::{next(_episode_counter):06d}",
            source_state_id=event.source_state_id,
            target_state_ids=list(event.candidate_target_states),
            anchors_used=[a.anchor_id for a in anchors],
            ambiguity_signature=signature,
            identity_shift_delta=identity_shift_delta or {},
        )
        self._episodes.append(episode)
        self._index[self.signature_key(signature)].append(episode.episode_id)
        return episode

    # ------------------------------------------------------------------
    @staticmethod
    def compute_signature(field: AmbiguityField) -> dict[str, Any]:
        """Compact structural summary of an ambiguity field."""
        densities = [r.conflict_density for r in field.regions] or [0.0]
        dominant = (
            max(field.gradients, key=field.gradients.get)
            if field.gradients
            else None
        )
        return {
            "region_count": len(field.regions),
            "void_count": len(field.voids),
            "island_count": len(field.coherence_islands),
            "conflict_edge_count": sum(
                len(v) for v in field.conflict_topology.values()
            )
            // 2,
            "mean_conflict_density": round(sum(densities) / len(densities), 4),
            "dominant_gradient": dominant,
        }

    @staticmethod
    def signature_key(signature: dict[str, Any]) -> str:
        """Hashable bucket key. Coarse by design — Phase 2 replaces this
        with embedding similarity."""
        return (
            f"r{signature['region_count']}"
            f"-v{signature['void_count']}"
            f"-i{signature['island_count']}"
            f"-c{signature['conflict_edge_count']}"
        )

    # ------------------------------------------------------------------
    def retrieve_similar(self, field: AmbiguityField) -> list[LiminalMemoryEpisode]:
        """Phase 1 retrieval: exact signature-bucket match."""
        key = self.signature_key(self.compute_signature(field))
        ids = set(self._index.get(key, []))
        return [e for e in self._episodes if e.episode_id in ids]

    def all_episodes(self) -> list[LiminalMemoryEpisode]:
        return list(self._episodes)

    def __len__(self) -> int:
        return len(self._episodes)
