"""Unit tests for ProtoIntentSynthesizer — Contract #5: intent is
directional pressure, never a decision."""

from __future__ import annotations

import dataclasses

from lae.intent.proto_intent_synthesizer import ProtoIntentSynthesizer
from lae.types import LiminalMemoryEpisode


def make_episode(eid: str, targets: list[str]) -> LiminalMemoryEpisode:
    return LiminalMemoryEpisode(
        episode_id=eid,
        source_state_id="src",
        target_state_ids=targets,
        anchors_used=[],
        ambiguity_signature={},
        identity_shift_delta={},
    )


def test_no_history_neutral_stability(make_field):
    intent = ProtoIntentSynthesizer().synthesize(make_field(), [])
    assert intent.stability_score == 0.5
    assert intent.origin_episode_ids == []


def test_vector_derived_from_field_gradients(make_field):
    field = make_field(profile={"a": 0.4, "b": 0.3})
    intent = ProtoIntentSynthesizer().synthesize(field, [])
    assert set(field.gradients) <= set(intent.vector)


def test_history_agreement_raises_stability(make_field):
    field = make_field(profile={"a": 0.4, "b": 0.3})
    # History points where the field already leans (toward "a").
    episodes = [make_episode("episode::1", ["a", "b"])]
    intent = ProtoIntentSynthesizer().synthesize(field, episodes)
    assert intent.stability_score == 0.9
    assert "episode::1" in intent.origin_episode_ids


def test_history_disagreement_lowers_stability(make_field):
    field = make_field(profile={"a": 0.4, "b": 0.3})
    episodes = [make_episode("episode::1", ["b", "a"])]
    intent = ProtoIntentSynthesizer().synthesize(field, episodes)
    assert intent.stability_score == 0.2


def test_magnitude_is_l2_norm(make_field):
    import math

    field = make_field()
    intent = ProtoIntentSynthesizer().synthesize(field, [])
    expected = round(math.sqrt(sum(v * v for v in intent.vector.values())), 4)
    assert intent.magnitude == expected


def test_intent_is_non_decisional(make_field):
    """Contract #5: the ProtoIntent carries only directional fields —
    no chosen target, no committed action, no resolution."""
    intent = ProtoIntentSynthesizer().synthesize(make_field(), [])
    field_names = {f.name for f in dataclasses.fields(intent)}
    assert field_names == {
        "vector", "magnitude", "stability_score",
        "origin_episode_ids", "ambiguity_lineage",
    }


def test_ambiguity_lineage_covers_field(make_field):
    field = make_field()
    intent = ProtoIntentSynthesizer().synthesize(field, [])
    assert intent.ambiguity_lineage == [r.id for r in field.regions]
