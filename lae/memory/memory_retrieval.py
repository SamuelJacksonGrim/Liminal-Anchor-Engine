"""
lae.memory.memory_retrieval — Similarity-based retrieval + anchor suggestion (Phase 2).

Two responsibilities:
1. top_k_similar(field) — retrieve the k most structurally similar past
   episodes using the AmbiguitySignatureIndex.
2. suggest_anchors(episodes) — look at which anchors have been used in
   similar past crossings and suggest them for the current one. This is
   the pattern-based anchor suggestion item from the Phase 2 roadmap.

Anchor suggestion is advisory only — the AnchorAllocator still owns
allocation. The suggestions are passed as hints; the allocator may use
or ignore them. Contract #3 is never violated: suggested anchors are
constraints, not state.
"""

from __future__ import annotations

from collections import Counter

from ..types import AmbiguityField, Anchor, LiminalMemoryEpisode
from .ambiguity_signature_index import AmbiguitySignatureIndex
from .transition_episode_store import TransitionEpisodeStore


class MemoryRetrieval:
    DEFAULT_K = 5
    SUGGESTION_MIN_VOTES = 2  # anchor must appear in >=2 similar episodes to suggest

    def __init__(
        self,
        store: TransitionEpisodeStore,
        index: AmbiguitySignatureIndex,
    ) -> None:
        self.store = store
        self.index = index

    # ------------------------------------------------------------------
    def top_k_similar(
        self, field: AmbiguityField, k: int = DEFAULT_K
    ) -> list[LiminalMemoryEpisode]:
        """Return up to k episodes most similar to the given field."""
        from .liminal_memory_buffer import LiminalMemoryBuffer

        sig = LiminalMemoryBuffer.compute_signature(field)
        ranked = self.index.top_k(sig, k=k)
        ids = [eid for eid, _score in ranked]
        return self.store.get_many(ids)

    # ------------------------------------------------------------------
    def suggest_anchors(
        self,
        similar_episodes: list[LiminalMemoryEpisode],
        current_anchors: list[Anchor],
    ) -> list[str]:
        """Return anchor IDs from history that frequently co-occurred with
        similar transitions and are not already active.

        Returns a list of anchor_id strings (references to past anchors)
        that the allocator may use as templates when allocating new ones.
        """
        if not similar_episodes:
            return []

        current_ids = {a.anchor_id for a in current_anchors}
        counter: Counter[str] = Counter()
        for ep in similar_episodes:
            for aid in ep.anchors_used:
                counter[aid] += 1

        suggestions = [
            aid
            for aid, count in counter.most_common()
            if count >= self.SUGGESTION_MIN_VOTES and aid not in current_ids
        ]
        return suggestions

    # ------------------------------------------------------------------
    def episode_ids_by_source(self, source_state_id: str) -> list[str]:
        """All episode IDs that originated from a given source state."""
        return [
            ep.episode_id
            for ep in self.store.all()
            if ep.source_state_id == source_state_id
        ]
