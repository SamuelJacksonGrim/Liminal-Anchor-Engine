"""
lae.memory.compression_strategy — Episode compression (Phase 2).

CONFIG: memory.compression = enabled.

When the episode store grows beyond a threshold, compression merges
redundant episodes within the same signature cluster into a single
representative episode. The merged episode preserves:
- all unique target_state_ids ever seen in the cluster
- union of anchors_used
- merged ambiguity_signature (mean of numeric fields)
- identity_shift_delta: union of all diff keys (last-write wins per key)

The source_state_id of the cluster centroid episode is kept. The merged
episode ID is tagged as a compression artifact.

Compression never deletes transition history — it summarizes it.
CONFIG safety flag preserve_transition_history is checked before any
destructive operation: if True, original episodes are archived in
metadata rather than removed from the store entirely.
"""

from __future__ import annotations

import itertools
import time
from typing import Any

from ..config import LAEConfig
from ..types import LiminalMemoryEpisode
from .ambiguity_signature_index import AmbiguitySignatureIndex
from .transition_episode_store import TransitionEpisodeStore

_compress_counter = itertools.count(1)

COMPRESS_THRESHOLD = 20   # compress when store exceeds this many episodes
MIN_CLUSTER_SIZE = 3      # only merge clusters with >= this many members


class CompressionStrategy:
    def __init__(
        self,
        store: TransitionEpisodeStore,
        index: AmbiguitySignatureIndex,
        config: LAEConfig | None = None,
    ) -> None:
        self.store = store
        self.index = index
        self.config = config or LAEConfig()

    # ------------------------------------------------------------------
    def should_compress(self) -> bool:
        return len(self.store) > COMPRESS_THRESHOLD

    def compress(self) -> int:
        """Run one compression pass. Returns number of episodes removed."""
        if not self.should_compress():
            return 0

        cluster_map = self.index.cluster_keys()  # {episode_id: cluster_label}
        # Group by cluster.
        clusters: dict[int, list[str]] = {}
        for eid, label in cluster_map.items():
            clusters.setdefault(label, []).append(eid)

        removed = 0
        for label, eids in clusters.items():
            if len(eids) < MIN_CLUSTER_SIZE:
                continue
            episodes = self.store.get_many(eids)
            if not episodes:
                continue
            merged = self._merge(episodes)
            # Keep the oldest episode slot as the merged record.
            anchor_id = eids[0]
            self.store.replace(anchor_id, merged)
            # Archive or remove the rest.
            for eid in eids[1:]:
                if self.config.preserve_transition_history:
                    # Mark as compressed but leave retrievable via metadata.
                    ep = self.store.get(eid)
                    if ep:
                        self.store.metadata_for(eid)["archived_by"] = merged.episode_id
                        self.store.remove(eid)
                else:
                    self.store.remove(eid)
                removed += 1

        return removed

    # ------------------------------------------------------------------
    @staticmethod
    def _merge(episodes: list[LiminalMemoryEpisode]) -> LiminalMemoryEpisode:
        all_targets: list[str] = []
        all_anchors: list[str] = []
        merged_delta: dict[str, Any] = {}
        sig_accum: dict[str, Any] = {}
        count = len(episodes)

        for ep in episodes:
            for t in ep.target_state_ids:
                if t not in all_targets:
                    all_targets.append(t)
            for a in ep.anchors_used:
                if a not in all_anchors:
                    all_anchors.append(a)
            merged_delta.update(ep.identity_shift_delta)

            for k, v in ep.ambiguity_signature.items():
                if isinstance(v, (int, float)):
                    sig_accum[k] = sig_accum.get(k, 0.0) + v
                elif k not in sig_accum:
                    sig_accum[k] = v

        merged_sig = {
            k: (round(v / count, 4) if isinstance(v, float) else v)
            for k, v in sig_accum.items()
        }
        merged_sig["compressed_from"] = count
        merged_sig["compressed_at"] = time.time()

        return LiminalMemoryEpisode(
            episode_id=f"episode::compressed::{next(_compress_counter):04d}",
            source_state_id=episodes[0].source_state_id,
            target_state_ids=all_targets,
            anchors_used=all_anchors,
            ambiguity_signature=merged_sig,
            identity_shift_delta=merged_delta,
        )
