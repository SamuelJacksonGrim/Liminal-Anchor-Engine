"""Unit tests for LiminalMemoryBuffer — Contract #4: memory stores
crossings, not snapshots."""

from __future__ import annotations

from lae.anchors.anchor_allocator import AnchorAllocator
from lae.memory.liminal_memory_buffer import LiminalMemoryBuffer


def record_one(buffer, make_event, make_field, **kwargs):
    event = make_event(**kwargs)
    field = make_field(**kwargs)
    anchors = AnchorAllocator().allocate(field)
    return buffer.record(event=event, field=field, anchors=anchors), field


def test_record_returns_episode(make_event, make_field):
    buffer = LiminalMemoryBuffer()
    episode, _ = record_one(buffer, make_event, make_field)
    assert episode.episode_id.startswith("episode::")
    assert len(buffer) == 1


def test_episode_stores_crossing_not_snapshot(make_event, make_field):
    """Contract #4: the episode references source and targets by ID and
    carries the ambiguity signature — never full state objects."""
    buffer = LiminalMemoryBuffer()
    episode, _ = record_one(buffer, make_event, make_field, source="A")
    assert episode.source_state_id == "A"
    assert all(isinstance(t, str) for t in episode.target_state_ids)
    assert isinstance(episode.ambiguity_signature, dict)
    assert all(isinstance(a, str) for a in episode.anchors_used)


def test_signature_structure(make_field):
    sig = LiminalMemoryBuffer.compute_signature(make_field())
    assert {"region_count", "void_count", "island_count",
            "conflict_edge_count", "mean_conflict_density",
            "dominant_gradient"} <= set(sig)


def test_retrieve_similar_finds_prior_crossing(make_event, make_field):
    buffer = LiminalMemoryBuffer()
    episode, field = record_one(buffer, make_event, make_field)
    similar = buffer.retrieve_similar(field)
    assert any(ep.episode_id == episode.episode_id for ep in similar)


def test_retrieve_similar_empty_memory(make_field):
    buffer = LiminalMemoryBuffer()
    assert buffer.retrieve_similar(make_field()) == []


def test_suggest_anchors_returns_list(make_event, make_field):
    buffer = LiminalMemoryBuffer()
    record_one(buffer, make_event, make_field)
    field = make_field()
    suggestions = buffer.suggest_anchors(field, current_anchors=[])
    assert isinstance(suggestions, list)


def test_episode_ids_unique(make_event, make_field):
    buffer = LiminalMemoryBuffer()
    ids = {record_one(buffer, make_event, make_field)[0].episode_id for _ in range(5)}
    assert len(ids) == 5
