"""
lae.identity.invariance_tracker — Feature invariance discovery (Phase 3).

Watches the protected_features of anchors across episodes. A feature
graduates to invariant when it has been continuously protected across a
minimum fraction of observed transitions — it is never mutated, only
guarded.

Design: streaming over episodes, no full replay required. Maintains
counters per feature and recomputes invariant candidates on demand.
"""

from __future__ import annotations

from collections import defaultdict

from ..types import LiminalMemoryEpisode

INVARIANCE_THRESHOLD = 0.75   # protected in >= 75% of episodes -> invariant candidate
MIN_EPISODES = 5              # don't declare invariants until enough data


class InvarianceTracker:
    def __init__(self) -> None:
        self._episode_count = 0
        self._protection_count: dict[str, int] = defaultdict(int)
        # Track features that have ever been in forbidden_mutations (disqualified).
        self._ever_mutated: set[str] = set()

    # ------------------------------------------------------------------
    def observe(self, episode: LiminalMemoryEpisode) -> None:
        """Process one episode. Called by the mapper after each recording."""
        self._episode_count += 1
        sig = episode.ambiguity_signature
        protected = sig.get("protected_features", [])
        forbidden_seen = sig.get("forbidden_mutations_seen", [])

        for feat in protected:
            self._protection_count[feat] += 1
        for feat in forbidden_seen:
            self._ever_mutated.add(feat)

    # ------------------------------------------------------------------
    def invariant_candidates(self) -> list[str]:
        """Features that qualify as invariants given observed history."""
        if self._episode_count < MIN_EPISODES:
            return []
        threshold_count = int(self._episode_count * INVARIANCE_THRESHOLD)
        return [
            feat
            for feat, count in self._protection_count.items()
            if count >= threshold_count and feat not in self._ever_mutated
        ]

    def protection_rate(self, feature: str) -> float:
        if self._episode_count == 0:
            return 0.0
        return self._protection_count[feature] / self._episode_count
