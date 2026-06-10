"""
lae.multimind.collective_intent — Collective proto-intent synthesis (Phase 4).

Combines per-agent ProtoIntents into one collective lean.

Contract #5 still binds at the collective level: the output is
directional only. The collective does not vote a decision into
existence — it synthesizes a shared lean with an honesty term:

- vector: weighted mean of agent vectors.
- magnitude: norm of the merged vector. NOTE: opposing agent leans
  partially cancel — a collective torn in two directions has LOWER
  magnitude than a unified one. This is intentional and honest: the
  collective genuinely leans less when its members disagree.
- stability_score: mean agent stability scaled by alignment. A
  collective of individually-stable but mutually-opposed agents is NOT
  stable. alignment = 1 - normalized pairwise divergence of top leans.
- origin_episode_ids / ambiguity_lineage: unions, provenance preserved.
"""

from __future__ import annotations

import math

from ..types import ProtoIntent


class CollectiveIntentSynthesizer:
    @staticmethod
    def synthesize(
        intents: dict[str, ProtoIntent],
        trust_weights: dict[str, float] | None = None,
    ) -> ProtoIntent:
        """Merge per-agent intents into one collective ProtoIntent.

        Args:
            intents: {agent_id: ProtoIntent}
            trust_weights: optional {agent_id: weight}; defaults uniform.
        """
        if not intents:
            return ProtoIntent(
                vector={}, magnitude=0.0, stability_score=0.5,
                origin_episode_ids=[], ambiguity_lineage=[],
            )
        if len(intents) == 1:
            return next(iter(intents.values()))

        agents = list(intents.keys())
        weights = trust_weights or {a: 1.0 for a in agents}
        total_w = sum(weights.get(a, 1.0) for a in agents) or 1.0

        # Weighted mean vector.
        merged_vector: dict[str, float] = {}
        for a in agents:
            w = weights.get(a, 1.0) / total_w
            for k, v in intents[a].vector.items():
                merged_vector[k] = merged_vector.get(k, 0.0) + v * w
        merged_vector = {k: round(v, 4) for k, v in merged_vector.items()}

        magnitude = round(
            math.sqrt(sum(v * v for v in merged_vector.values())), 4
        )

        # Alignment: do the agents lean the same way?
        tops = []
        for a in agents:
            if intents[a].vector:
                tops.append(max(intents[a].vector, key=intents[a].vector.get))
        if len(tops) >= 2:
            unique = len(set(tops))
            alignment = 1.0 - (unique - 1) / (len(tops) - 1)
        else:
            alignment = 1.0

        mean_stability = sum(i.stability_score for i in intents.values()) / len(intents)
        stability = round(mean_stability * alignment, 4)

        # Provenance unions.
        origins: list[str] = []
        lineage: list[str] = []
        for i in intents.values():
            for o in i.origin_episode_ids:
                if o not in origins:
                    origins.append(o)
            for l in i.ambiguity_lineage:
                if l not in lineage:
                    lineage.append(l)

        return ProtoIntent(
            vector=merged_vector,
            magnitude=magnitude,
            stability_score=stability,
            origin_episode_ids=origins,
            ambiguity_lineage=lineage,
        )
