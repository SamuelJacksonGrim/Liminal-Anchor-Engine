"""
lae.memory.ambiguity_signature_index — Signature-based episode indexing (Phase 2).

Replaces the coarse bucket key from Phase 1 with cosine similarity over
a 5-dimensional feature vector derived from the ambiguity signature:

    [region_count, void_count, island_count, conflict_edge_count,
     mean_conflict_density]

Each dimension is min-max normalized against the running observed range
so all features contribute equally regardless of scale. No external
dependencies — pure stdlib math.

The index supports:
- insert(episode_id, signature) — add to index
- top_k(signature, k) — return k most similar episode_ids
- cluster_keys() — return current centroid labels (for compression)
"""

from __future__ import annotations

import math
from typing import Any


def _to_vector(sig: dict[str, Any]) -> list[float]:
    """Extract the 5-dimensional feature vector from a signature."""
    return [
        float(sig.get("region_count", 0)),
        float(sig.get("void_count", 0)),
        float(sig.get("island_count", 0)),
        float(sig.get("conflict_edge_count", 0)),
        float(sig.get("mean_conflict_density", 0.0)),
    ]


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a == 0 or mag_b == 0:
        return 1.0 if a == b else 0.0
    return dot / (mag_a * mag_b)


class AmbiguitySignatureIndex:
    def __init__(self, scan_limit: int = 0) -> None:
        # episode_id -> raw vector (pre-normalization stored for re-norm)
        self._entries: list[tuple[str, list[float]]] = []
        # Running min/max per dimension for normalization
        self._mins: list[float] = [float("inf")] * 5
        self._maxs: list[float] = [float("-inf")] * 5
        # Cap the linear similarity scan to the most-recent N entries so
        # top_k stays O(1) per call as memory grows. 0 = unbounded (scan all).
        # Entries are appended in insertion order, so the newest are last.
        self.scan_limit = scan_limit

    # ------------------------------------------------------------------
    def insert(self, episode_id: str, signature: dict[str, Any]) -> None:
        vec = _to_vector(signature)
        self._entries.append((episode_id, vec))
        for i, v in enumerate(vec):
            if v < self._mins[i]:
                self._mins[i] = v
            if v > self._maxs[i]:
                self._maxs[i] = v

    def top_k(
        self, signature: dict[str, Any], k: int = 5
    ) -> list[tuple[str, float]]:
        """Return up to k (episode_id, similarity) pairs, best first."""
        if not self._entries:
            return []
        query = self._normalize(_to_vector(signature))
        entries = self._entries
        if self.scan_limit and len(entries) > self.scan_limit:
            entries = entries[-self.scan_limit :]
        scored = [
            (eid, _cosine(query, self._normalize(vec)))
            for eid, vec in entries
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:k]

    def cluster_keys(self, n_clusters: int = 4) -> dict[str, int]:
        """Assign each episode to a cluster via k-means (k=n_clusters).

        Returns {episode_id: cluster_label}. Used by compression to
        merge redundant episodes within the same cluster.
        """
        if len(self._entries) < n_clusters:
            return {eid: 0 for eid, _ in self._entries}

        vecs = [self._normalize(v) for _, v in self._entries]
        ids = [eid for eid, _ in self._entries]

        # Initialize centroids as first n_clusters unique vectors.
        centroids = [list(v) for v in vecs[:n_clusters]]

        for _ in range(20):  # max iterations
            assignments: list[int] = []
            for v in vecs:
                best = max(range(n_clusters), key=lambda c: _cosine(v, centroids[c]))
                assignments.append(best)

            new_centroids = []
            for c in range(n_clusters):
                members = [vecs[i] for i, a in enumerate(assignments) if a == c]
                if not members:
                    new_centroids.append(centroids[c])
                else:
                    dims = len(members[0])
                    mean = [sum(m[d] for m in members) / len(members) for d in range(dims)]
                    new_centroids.append(mean)

            if new_centroids == centroids:
                break
            centroids = new_centroids

        return {ids[i]: assignments[i] for i in range(len(ids))}

    # ------------------------------------------------------------------
    def _normalize(self, vec: list[float]) -> list[float]:
        out = []
        for i, v in enumerate(vec):
            lo, hi = self._mins[i], self._maxs[i]
            if hi == lo:
                out.append(0.0)
            else:
                out.append((v - lo) / (hi - lo))
        return out

    def __len__(self) -> int:
        return len(self._entries)
