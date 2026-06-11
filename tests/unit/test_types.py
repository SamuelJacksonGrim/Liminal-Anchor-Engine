"""Canonical type contract tests.

Verifies the dataclasses in lae/types.py stay in lockstep with the JSON
schemas in schemas/ (Contract #0) and that every type serializes to the
schema-shaped dict via dataclasses.asdict.
"""

from __future__ import annotations

import dataclasses
import json
from pathlib import Path

import pytest

from lae.types import (
    AmbiguityField,
    Anchor,
    IdentityGradient,
    LiminalMemoryEpisode,
    ProtoIntent,
    Region,
    TimeWindow,
    TransitionEvent,
)

SCHEMA_DIR = Path(__file__).resolve().parent.parent.parent / "schemas"

TYPE_TO_SCHEMA = [
    (TransitionEvent, "transition_schema.json"),
    (AmbiguityField, "ambiguity_field_schema.json"),
    (Anchor, "anchor_schema.json"),
    (LiminalMemoryEpisode, "liminal_memory_episode_schema.json"),
    (ProtoIntent, "proto_intent_schema.json"),
    (IdentityGradient, "identity_gradient_schema.json"),
]


def load_schema(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


@pytest.mark.parametrize("dc,schema_file", TYPE_TO_SCHEMA)
def test_dataclass_fields_match_schema_properties(dc, schema_file):
    schema = load_schema(schema_file)
    dc_fields = {f.name for f in dataclasses.fields(dc)}
    schema_props = set(schema["properties"].keys())
    assert dc_fields == schema_props, (
        f"{dc.__name__} fields {dc_fields} != {schema_file} properties {schema_props}"
    )


@pytest.mark.parametrize("dc,schema_file", TYPE_TO_SCHEMA)
def test_schema_required_subset_of_fields(dc, schema_file):
    schema = load_schema(schema_file)
    dc_fields = {f.name for f in dataclasses.fields(dc)}
    assert set(schema.get("required", [])) <= dc_fields


def test_time_window_serializes_to_schema_shape():
    event = TransitionEvent(
        source_state_id="s",
        candidate_target_states=["a"],
        confidence_profile={"a": 0.3},
        conflict_score=0.5,
        time_window=TimeWindow(start=1.0, end=2.5),
    )
    as_dict = dataclasses.asdict(event)
    assert as_dict["time_window"] == {"start": 1.0, "end": 2.5}
    # Round-trips through JSON without custom encoders.
    json.dumps(as_dict)


def test_time_window_duration():
    assert TimeWindow(start=1.0, end=2.5).duration() == 1.5


def test_ambiguity_field_region_by_id():
    region = Region(
        id="r1", conflict_density=0.1, coherence_score=0.9,
        semantic_tags=[], neighbors=[],
    )
    field = AmbiguityField(regions=[region])
    assert field.region_by_id("r1") is region
    assert field.region_by_id("missing") is None


def test_ambiguity_field_defaults_are_independent():
    f1 = AmbiguityField(regions=[])
    f2 = AmbiguityField(regions=[])
    f1.voids.append("x")
    assert f2.voids == []
