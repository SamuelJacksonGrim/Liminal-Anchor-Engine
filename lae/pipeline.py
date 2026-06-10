"""
lae.pipeline — Phase 1 end-to-end pipeline.

Wires the Phase 1 layers in CONFIG.yaml pipeline order:

    observation -> TransitionDetector -> TransitionEvent
                -> AmbiguityFieldGenerator -> AmbiguityField
                -> AnchorAllocator -> [Anchor]
                -> LiminalMemoryBuffer -> LiminalMemoryEpisode
                -> ProtoIntentSynthesizer -> ProtoIntent

IdentityGradientMapper and EventRouter are Phase 3/5 per the roadmap —
the pipeline exposes their seams (identity_shift_delta passthrough,
LiminalResult event object) without implementing them.

Activation is event-triggered (CONFIG: activation.mode). If no trigger
fires on an observation, the pipeline returns None and nothing
downstream runs. The engine only exists in transitions.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .anchors.anchor_allocator import AnchorAllocator
from .config import LAEConfig, load_config
from .detectors.transition_detector import TransitionDetector
from .fields.ambiguity_field import AmbiguityFieldGenerator
from .intent.proto_intent_synthesizer import ProtoIntentSynthesizer
from .memory.liminal_memory_buffer import LiminalMemoryBuffer
from .types import (
    AmbiguityField,
    Anchor,
    LiminalMemoryEpisode,
    ProtoIntent,
    TransitionEvent,
)


@dataclass
class LiminalResult:
    """Everything one liminal activation produced. Phase 5's EventRouter
    will consume this; for now it is the pipeline's return value."""

    event: TransitionEvent
    field: AmbiguityField
    anchors: list[Anchor]
    episode: LiminalMemoryEpisode
    intent: ProtoIntent


class LiminalAnchorEngine:
    """Phase 1 minimal functional skeleton, end to end."""

    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or load_config()
        self.detector = TransitionDetector(self.config)
        self.field_generator = AmbiguityFieldGenerator(self.config)
        self.anchor_allocator = AnchorAllocator(self.config)
        self.memory = LiminalMemoryBuffer(self.config)
        self.intent_synthesizer = ProtoIntentSynthesizer(self.config)

    def process(self, observation: dict[str, Any]) -> LiminalResult | None:
        """Run one observation through the full Phase 1 pipeline.

        Returns None when no transition trigger fires (the engine is
        event-triggered and dormant outside liminal windows).
        """
        event = self.detector.observe(observation)
        if event is None:
            return None

        field = self.field_generator.generate(event)

        anchors = self.anchor_allocator.allocate(field)

        # Retrieve BEFORE recording so the current crossing does not
        # count as its own precedent.
        similar = self.memory.retrieve_similar(field)

        episode = self.memory.record(
            event=event,
            field=field,
            anchors=anchors,
            identity_shift_delta={},  # Phase 3: IdentityGradientMapper
        )

        intent = self.intent_synthesizer.synthesize(field, similar)

        return LiminalResult(
            event=event,
            field=field,
            anchors=anchors,
            episode=episode,
            intent=intent,
        )
