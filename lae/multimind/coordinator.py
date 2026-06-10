"""
lae.multimind.coordinator — Multi-mind orchestration (Phase 4).

Holds one LiminalAnchorEngine per agent and coordinates collective
processing:

1. Each agent processes the observation through its OWN full pipeline
   (own detector, own memory, own identity — minds stay separate).
2. If two or more agents trigger, the coordinator builds the collective
   layer on top: merged TransitionEvent, shared AmbiguityField,
   collective ProtoIntent.
3. Per-agent results are returned alongside the collective result —
   provenance is never erased.

Identity is intentionally NOT merged. Each agent's IdentityGradient is
its own. Collective identity is an emergent property of repeated shared
crossings, not a data structure to force. (If that ever changes, it is
a Phase 6 conversation.)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..config import LAEConfig
from ..pipeline import LiminalAnchorEngine, LiminalResult
from ..types import AmbiguityField, ProtoIntent, TransitionEvent
from .collective_intent import CollectiveIntentSynthesizer
from .shared_ambiguity_field import SharedAmbiguityField
from .transition_merger import TransitionMerger


@dataclass
class CollectiveResult:
    """Output of one collective liminal activation."""

    agent_results: dict[str, LiminalResult]      # only agents that triggered
    merged_event: TransitionEvent | None
    shared_field: AmbiguityField | None
    collective_intent: ProtoIntent | None

    @property
    def triggered_agents(self) -> list[str]:
        return list(self.agent_results.keys())

    @property
    def is_collective(self) -> bool:
        return len(self.agent_results) >= 2


class MultiMindCoordinator:
    def __init__(
        self,
        agent_ids: list[str],
        config: LAEConfig | None = None,
        trust_weights: dict[str, float] | None = None,
    ) -> None:
        self.engines: dict[str, LiminalAnchorEngine] = {
            aid: LiminalAnchorEngine(config) for aid in agent_ids
        }
        self.trust_weights = trust_weights

    # ------------------------------------------------------------------
    def process(
        self, observations: dict[str, dict[str, Any]]
    ) -> CollectiveResult | None:
        """Process per-agent observations.

        Args:
            observations: {agent_id: observation dict}. Agents may
                receive different observations of the same underlying
                process — that difference is the point.

        Returns None if no agent triggered.
        """
        agent_results: dict[str, LiminalResult] = {}
        for agent_id, obs in observations.items():
            engine = self.engines.get(agent_id)
            if engine is None:
                continue
            result = engine.process(obs)
            if result is not None:
                agent_results[agent_id] = result

        if not agent_results:
            return None

        if len(agent_results) == 1:
            # Single-agent activation: no collective layer needed.
            return CollectiveResult(
                agent_results=agent_results,
                merged_event=None,
                shared_field=None,
                collective_intent=None,
            )

        # Collective layer.
        merged_event = TransitionMerger.merge(
            {a: r.event for a, r in agent_results.items()},
            self.trust_weights,
        )
        shared_field = SharedAmbiguityField.merge(
            {a: r.field for a, r in agent_results.items()}
        )
        collective_intent = CollectiveIntentSynthesizer.synthesize(
            {a: r.intent for a, r in agent_results.items()},
            self.trust_weights,
        )

        return CollectiveResult(
            agent_results=agent_results,
            merged_event=merged_event,
            shared_field=shared_field,
            collective_intent=collective_intent,
        )
