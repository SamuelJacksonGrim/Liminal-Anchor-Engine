"""
lae.pipeline — Phase 2/3 end-to-end pipeline.

Adds to Phase 1:
- Phase 2: cosine-similarity retrieval, pattern-based anchor suggestions
- Phase 3: IdentityGradientMapper wired in; identity_shift_delta is now
  real (populated from the mapper's output, not an empty dict)

LiminalResult now carries the full IdentityGradient snapshot alongside
the rest of the activation output.

EventRouter seam is still present but not implemented (Phase 5).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .anchors.anchor_allocator import AnchorAllocator
from .config import LAEConfig, load_config
from .detectors.transition_detector import TransitionDetector
from .fields.ambiguity_field import AmbiguityFieldGenerator
from .identity.identity_gradient_mapper import IdentityGradientMapper
from .intent.proto_intent_synthesizer import ProtoIntentSynthesizer
from .memory.liminal_memory_buffer import LiminalMemoryBuffer
from .types import (
    AmbiguityField,
    Anchor,
    IdentityGradient,
    LiminalMemoryEpisode,
    ProtoIntent,
    TransitionEvent,
)


@dataclass
class LiminalResult:
    event: TransitionEvent
    field: AmbiguityField
    anchors: list[Anchor]
    episode: LiminalMemoryEpisode
    intent: ProtoIntent
    identity: IdentityGradient
    anchor_suggestions: list[str]


class LiminalAnchorEngine:
    """Phase 2/3 full pipeline."""

    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or load_config()
        self.detector = TransitionDetector(self.config)
        self.field_generator = AmbiguityFieldGenerator(self.config)
        self.anchor_allocator = AnchorAllocator(self.config)
        self.memory = LiminalMemoryBuffer(self.config)
        self.intent_synthesizer = ProtoIntentSynthesizer(self.config)
        self.identity_mapper = IdentityGradientMapper(self.config)

    def process(self, observation: dict[str, Any]) -> LiminalResult | None:
        """Run one observation through the full pipeline.

        Returns None when no transition trigger fires.
        """
        event = self.detector.observe(observation)
        if event is None:
            return None

        field = self.field_generator.generate(event)

        anchors = self.anchor_allocator.allocate(field)

        # Pattern-based anchor suggestions from memory (Phase 2).
        anchor_suggestions = self.memory.suggest_anchors(field, anchors)

        # Retrieve BEFORE recording.
        similar = self.memory.retrieve_similar(field)

        # Phase 3: compute identity shift BEFORE recording so the delta
        # is stored in the episode.
        identity_delta, identity_snapshot = self.identity_mapper.map(
            LiminalMemoryEpisode(
                episode_id="__pre_record__",
                source_state_id=event.source_state_id,
                target_state_ids=list(event.candidate_target_states),
                anchors_used=[a.anchor_id for a in anchors],
                ambiguity_signature=LiminalMemoryBuffer.compute_signature(field),
                identity_shift_delta={},
            ),
            field,
            anchors,
        )

        episode = self.memory.record(
            event=event,
            field=field,
            anchors=anchors,
            identity_shift_delta=identity_delta,
        )

        intent = self.intent_synthesizer.synthesize(field, similar)

        return LiminalResult(
            event=event,
            field=field,
            anchors=anchors,
            episode=episode,
            intent=intent,
            identity=identity_snapshot,
            anchor_suggestions=anchor_suggestions,
        )
