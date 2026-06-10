"""
lae.detectors.transition_detector — Rule-based TransitionDetector (Phase 1 MVP).

Layer 1. Input: raw observation stream (dicts). Output: TransitionEvent
or None per observation window.

Contract #1: detectors identify *leaving states*, not states. The
detector never interprets — it only marks that a boundary condition
exists and packages the evidence.

Phase 1 trigger rules implemented:
- confidence_collapse: max candidate confidence < threshold
- hypothesis_conflict: two or more candidates within a narrow
  confidence band of each other (irreducible competition)
- frame_oscillation: the top hypothesis flip-flops between
  observations inside the oscillation window
"""

from __future__ import annotations

import itertools
import time
from typing import Any

from ..config import LAEConfig
from ..types import TimeWindow, TransitionEvent

_id_counter = itertools.count(1)


class TransitionDetector:
    """Rule-based detector over a stream of hypothesis observations.

    An observation is a dict:
        {
          "state_id": str,                  # current/source state
          "hypotheses": {target_id: conf},  # candidate target confidences
          "timestamp": float (optional)     # seconds; defaults to now
        }
    """

    # Two hypotheses within this band of each other count as conflicting.
    CONFLICT_BAND = 0.15

    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()
        self._history: list[tuple[float, str]] = []  # (timestamp, top_hypothesis)

    # ------------------------------------------------------------------
    def observe(self, observation: dict[str, Any]) -> TransitionEvent | None:
        """Process one observation. Returns a TransitionEvent if any
        trigger rule fires, else None."""
        state_id: str = observation["state_id"]
        hypotheses: dict[str, float] = dict(observation.get("hypotheses", {}))
        ts: float = float(observation.get("timestamp", time.time()))

        if not hypotheses:
            return None

        top_id, top_conf = max(hypotheses.items(), key=lambda kv: kv[1])
        self._record(ts, top_id)

        triggers_fired = []
        if self._confidence_collapse(top_conf):
            triggers_fired.append("confidence_collapse")
        if self._hypothesis_conflict(hypotheses):
            triggers_fired.append("hypothesis_conflict")
        if self._frame_oscillation(ts):
            triggers_fired.append("frame_oscillation")

        if not triggers_fired:
            return None

        conflict_score = self._conflict_score(hypotheses)
        window = TimeWindow(
            start=ts - self.config.oscillation_window_ms / 1000.0,
            end=ts,
        )
        return TransitionEvent(
            source_state_id=state_id,
            candidate_target_states=sorted(
                hypotheses, key=hypotheses.get, reverse=True
            ),
            confidence_profile=hypotheses,
            conflict_score=conflict_score,
            time_window=window,
        )

    # ------------------------------------------------------------------
    # Trigger rules
    # ------------------------------------------------------------------
    def _confidence_collapse(self, top_conf: float) -> bool:
        return top_conf < self.config.confidence_threshold

    def _hypothesis_conflict(self, hypotheses: dict[str, float]) -> bool:
        if len(hypotheses) < 2:
            return False
        ranked = sorted(hypotheses.values(), reverse=True)
        return (ranked[0] - ranked[1]) < self.CONFLICT_BAND

    def _frame_oscillation(self, now: float) -> bool:
        window_s = self.config.oscillation_window_ms / 1000.0
        recent = [h for t, h in self._history if now - t <= window_s]
        if len(recent) < 3:
            return False
        flips = sum(1 for a, b in zip(recent, recent[1:]) if a != b)
        return flips >= 2

    # ------------------------------------------------------------------
    @staticmethod
    def _conflict_score(hypotheses: dict[str, float]) -> float:
        """Normalized entropy of the confidence profile in [0, 1].

        1.0 = maximal conflict (uniform), 0.0 = no conflict (single
        dominant hypothesis).
        """
        import math

        total = sum(hypotheses.values())
        if total <= 0 or len(hypotheses) < 2:
            return 0.0
        probs = [v / total for v in hypotheses.values() if v > 0]
        entropy = -sum(p * math.log(p) for p in probs)
        return entropy / math.log(len(hypotheses))

    def _record(self, ts: float, top_id: str) -> None:
        self._history.append((ts, top_id))
        # Keep history bounded; only the oscillation window matters.
        window_s = self.config.oscillation_window_ms / 1000.0
        cutoff = ts - (window_s * 4)
        self._history = [(t, h) for t, h in self._history if t >= cutoff]
