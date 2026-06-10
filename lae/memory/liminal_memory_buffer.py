"""
lae.memory.liminal_memory_buffer — Episodic buffer facade (Phase 2 upgrade).

Coordinates TransitionEpisodeStore, AmbiguitySignatureIndex,
MemoryRetrieval, and CompressionStrategy behind a single interface.
The pipeline only talks to this class — the submodules are implementation
details.

Phase 1 compatibility: compute_signature() and signature_key() are
preserved as static methods so ProtoIntentSynthesizer keeps working
without modification.
"""

from __future__ import annotations

from typing import Any

from ..config import LAEConfig
from ..types import AmbiguityField, Anchor, LiminalMemoryEpisode, TransitionEvent
from .ambiguity_signature_index import AmbiguitySignatureIndex
from .compression_strategy import CompressionStrategy
from .memory_retrieval import MemoryRetrieval
from .transition_episode_store import TransitionEpisodeStore

import itertools

_episode_counter = itertools.count(1)


class LiminalMemoryBuffer:
    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()
        self._store = TransitionEpisodeStore()
        self._index = AmbiguitySignatureIndex()
        self._retrieval = MemoryRetrieval(self._store, self._index)
        self._compression = CompressionStrategy(self._store, self._index, self.config)

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
        self._store.store(episode)
        self._index.insert(episode.episode_id, signature)

        # Opportunistic compression.
        if self._compression.should_compress():
            self._compression.compress()

        return episode

    # ------------------------------------------------------------------
    def retrieve_similar(
        self, field: AmbiguityField, k: int = 5
    ) -> list[LiminalMemoryEpisode]:
        """Top-k similarity retrieval (Phase 2: cosine similarity over
        ambiguity signature vectors)."""
        return self._retrieval.top_k_similar(field, k=k)

    def suggest_anchors(
        self,
        field: AmbiguityField,
        current_anchors: list[Anchor],
        k: int = 5,
    ) -> list[str]:
        """Pattern-based anchor suggestions from similar past episodes."""
        similar = self._retrieval.top_k_similar(field, k=k)
        return self._retrieval.suggest_anchors(similar, current_anchors)

    # ------------------------------------------------------------------
    @staticmethod
    def compute_signature(field: AmbiguityField) -> dict[str, Any]:
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
            ) // 2,
            "mean_conflict_density": round(sum(densities) / len(densities), 4),
            "dominant_gradient": dominant,
        }

    @staticmethod
    def signature_key(signature: dict[str, Any]) -> str:
        return (
            f"r{signature['region_count']}"
            f"-v{signature['void_count']}"
            f"-i{signature['island_count']}"
            f"-c{signature['conflict_edge_count']}"
        )

    # ------------------------------------------------------------------
    def all_episodes(self) -> list[LiminalMemoryEpisode]:
        return self._store.all()

    def __len__(self) -> int:
        return len(self._store)
