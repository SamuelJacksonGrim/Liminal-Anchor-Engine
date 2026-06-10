"""
lae.multimind.transition_merger — Cross-model transition merging +
conflict resolution (Phase 4).

Multiple agents observe the same underlying process and each emits its
own TransitionEvent. The merger combines them into one collective event
and resolves cross-agent conflicts WITHOUT erasing them:

Merging rules:
- source_state_id: majority vote. Dissenting sources are preserved in
  the merged confidence profile under "source_dissent::<agent>" keys —
  disagreement about where we even ARE is itself signal.
- candidate_target_states: union, ordered by combined confidence.
- confidence_profile: weighted mean per candidate. Weights default to
  uniform but accept per-agent trust weights.
- conflict_score: recomputed over the merged profile, then raised by a
  disagreement penalty proportional to cross-agent divergence. Two
  agents in perfect agreement add no penalty; agents leaning opposite
  ways raise collective conflict even if each is individually confident.
- time_window: envelope (earliest start, latest end).

Conflict resolution philosophy (matches Contract #2 applied across
minds): resolution here means *structuring* the disagreement so the
collective field can hold it — never picking a winner. The downstream
collective intent layer leans; it does not decide.
"""

from __future__ import annotations

from collections import Counter

from ..types import TimeWindow, TransitionEvent


class TransitionMerger:
    DISAGREEMENT_PENALTY_WEIGHT = 0.3

    @staticmethod
    def merge(
        events: dict[str, TransitionEvent],
        trust_weights: dict[str, float] | None = None,
    ) -> TransitionEvent:
        """Merge per-agent TransitionEvents into one collective event.

        Args:
            events: {agent_id: TransitionEvent}
            trust_weights: optional {agent_id: weight}; defaults uniform.
        """
        if not events:
            raise ValueError("cannot merge zero events")
        if len(events) == 1:
            return next(iter(events.values()))

        agents = list(events.keys())
        weights = trust_weights or {a: 1.0 for a in agents}
        total_w = sum(weights.get(a, 1.0) for a in agents) or 1.0

        # ------------------------------------------------------------------
        # Source: majority vote (weighted).
        source_votes: Counter[str] = Counter()
        for a in agents:
            source_votes[events[a].source_state_id] += weights.get(a, 1.0)
        merged_source = source_votes.most_common(1)[0][0]

        # ------------------------------------------------------------------
        # Confidence profile: weighted mean per candidate.
        merged_profile: dict[str, float] = {}
        for a in agents:
            w = weights.get(a, 1.0) / total_w
            for target, conf in events[a].confidence_profile.items():
                merged_profile[target] = merged_profile.get(target, 0.0) + conf * w

        # Preserve source dissent as signal.
        for a in agents:
            if events[a].source_state_id != merged_source:
                merged_profile[f"source_dissent::{a}"] = round(
                    weights.get(a, 1.0) / total_w, 4
                )

        merged_profile = {k: round(v, 4) for k, v in merged_profile.items()}

        # ------------------------------------------------------------------
        # Candidates: union ordered by merged confidence.
        candidates = sorted(
            {t for e in events.values() for t in e.candidate_target_states},
            key=lambda t: merged_profile.get(t, 0.0),
            reverse=True,
        )

        # ------------------------------------------------------------------
        # Conflict: entropy of merged profile + disagreement penalty.
        base_conflict = TransitionMerger._entropy_conflict(
            {k: v for k, v in merged_profile.items() if not k.startswith("source_dissent")}
        )
        divergence = TransitionMerger._cross_agent_divergence(events)
        merged_conflict = round(
            min(1.0, base_conflict + divergence * TransitionMerger.DISAGREEMENT_PENALTY_WEIGHT),
            4,
        )

        # ------------------------------------------------------------------
        # Time window: envelope.
        starts = [e.time_window.start for e in events.values()]
        ends = [e.time_window.end for e in events.values()]

        return TransitionEvent(
            source_state_id=merged_source,
            candidate_target_states=candidates,
            confidence_profile=merged_profile,
            conflict_score=merged_conflict,
            time_window=TimeWindow(start=min(starts), end=max(ends)),
        )

    # ------------------------------------------------------------------
    @staticmethod
    def _entropy_conflict(profile: dict[str, float]) -> float:
        import math

        total = sum(profile.values())
        if total <= 0 or len(profile) < 2:
            return 0.0
        probs = [v / total for v in profile.values() if v > 0]
        entropy = -sum(p * math.log(p) for p in probs)
        return entropy / math.log(len(profile))

    @staticmethod
    def _cross_agent_divergence(events: dict[str, TransitionEvent]) -> float:
        """How much agents disagree about the lean. 0 = identical top
        choices, 1 = everyone leans somewhere different."""
        tops = []
        for e in events.values():
            if e.confidence_profile:
                tops.append(max(e.confidence_profile, key=e.confidence_profile.get))
        if len(tops) < 2:
            return 0.0
        unique = len(set(tops))
        return (unique - 1) / (len(tops) - 1)
