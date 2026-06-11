"""
lae.identity.plasticity_analyzer — Plasticity zone identification (Phase 3).

A plasticity zone is a region of the identity field that changes
frequently. Operationally: any target state that appears in many
transitions is "plastic" — the system moves through it often, which
means identity in that direction is not settled.

Also tracks rigid dimensions: features consistently in the top gradient
direction across many crossings are rigid (the system always leans that
way — it is a stable attractor, not a transition zone).
"""

from __future__ import annotations

from collections import Counter

from ..types import LiminalMemoryEpisode

PLASTICITY_THRESHOLD = 0.3   # appears as target in >= 30% of episodes -> plastic
RIGIDITY_BASE = 0.1          # base rigidity increment per anchor protection
RIGIDITY_DECAY = 0.02        # per episode without protection


class PlasticityAnalyzer:
    def __init__(self) -> None:
        self._episode_count = 0
        self._target_counter: Counter[str] = Counter()
        self._rigidity_accum: dict[str, float] = {}
        self._last_seen: dict[str, int] = {}   # feature -> episode index last protected

    # ------------------------------------------------------------------
    def observe(self, episode: LiminalMemoryEpisode) -> None:
        idx = self._episode_count
        self._episode_count += 1

        for t in episode.target_state_ids:
            self._target_counter[t] += 1

        sig = episode.ambiguity_signature
        protected = sig.get("protected_features", [])
        for feat in protected:
            self._rigidity_accum[feat] = self._rigidity_accum.get(feat, 0.0) + RIGIDITY_BASE
            self._last_seen[feat] = idx

        # Apply decay for features not seen this episode.
        for feat in list(self._rigidity_accum):
            if feat not in protected:
                elapsed = idx - self._last_seen.get(feat, 0)
                decay = elapsed * RIGIDITY_DECAY
                self._rigidity_accum[feat] = max(0.0, self._rigidity_accum[feat] - decay)

    # ------------------------------------------------------------------
    def plasticity_zones(self) -> list[str]:
        """State IDs that appear as targets frequently enough to be plastic."""
        if self._episode_count == 0:
            return []
        threshold = self._episode_count * PLASTICITY_THRESHOLD
        return [t for t, count in self._target_counter.items() if count >= threshold]

    def rigidity_map(self) -> dict[str, float]:
        """Per-feature rigidity in [0, 1]."""
        return {
            feat: round(min(1.0, v), 4)
            for feat, v in self._rigidity_accum.items()
        }

    # ------------------------------------------------------------------
    def export_state(self) -> dict:
        return {
            "episode_count": self._episode_count,
            "target_counter": dict(self._target_counter),
            "rigidity_accum": dict(self._rigidity_accum),
            "last_seen": dict(self._last_seen),
        }

    def restore_state(self, state: dict) -> None:
        self._episode_count = int(state.get("episode_count", 0))
        self._target_counter = Counter(state.get("target_counter", {}))
        self._rigidity_accum = dict(state.get("rigidity_accum", {}))
        self._last_seen = {k: int(v) for k, v in state.get("last_seen", {}).items()}
