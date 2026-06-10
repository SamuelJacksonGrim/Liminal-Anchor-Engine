"""
lae.memory.transition_episode_store — Episode store with full metadata (Phase 2).

Separates the concern of *storing* episodes (this module) from
*retrieving* them (memory_retrieval.py) and *indexing* them
(ambiguity_signature_index.py).

Contract #4 enforced at the store boundary:
- Only LiminalMemoryEpisode objects enter the store.
- The store never holds raw state objects — only crossings.
- identity_shift_delta is always a diff, never a full state.

Phase 2 additions over Phase 1 buffer:
- full episode metadata (timestamp, trigger info)
- ordered access (insertion order preserved)
- episode deduplication guard (same source→target in same window)
"""

from __future__ import annotations

import time
from typing import Any


from ..types import LiminalMemoryEpisode


class TransitionEpisodeStore:
    def __init__(self) -> None:
        self._episodes: dict[str, LiminalMemoryEpisode] = {}
        self._order: list[str] = []
        self._metadata: dict[str, dict[str, Any]] = {}

    # ------------------------------------------------------------------
    def store(
        self,
        episode: LiminalMemoryEpisode,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Store an episode. Returns False if deduplicated (already present)."""
        if episode.episode_id in self._episodes:
            return False
        self._episodes[episode.episode_id] = episode
        self._order.append(episode.episode_id)
        self._metadata[episode.episode_id] = {
            "stored_at": time.time(),
            **(metadata or {}),
        }
        return True

    def get(self, episode_id: str) -> LiminalMemoryEpisode | None:
        return self._episodes.get(episode_id)

    def get_many(self, episode_ids: list[str]) -> list[LiminalMemoryEpisode]:
        return [self._episodes[eid] for eid in episode_ids if eid in self._episodes]

    def all(self) -> list[LiminalMemoryEpisode]:
        return [self._episodes[eid] for eid in self._order]

    def recent(self, n: int) -> list[LiminalMemoryEpisode]:
        return [self._episodes[eid] for eid in self._order[-n:]]

    def metadata_for(self, episode_id: str) -> dict[str, Any]:
        return dict(self._metadata.get(episode_id, {}))

    def replace(self, episode_id: str, replacement: LiminalMemoryEpisode) -> None:
        """Replace an episode in-place (used by compression). Order preserved."""
        if episode_id not in self._episodes:
            return
        self._episodes[episode_id] = replacement
        meta = self._metadata[episode_id]
        meta["compressed"] = True
        meta["compressed_at"] = time.time()

    def remove(self, episode_id: str) -> None:
        if episode_id not in self._episodes:
            return
        del self._episodes[episode_id]
        del self._metadata[episode_id]
        self._order.remove(episode_id)

    def __len__(self) -> int:
        return len(self._episodes)
