"""Unit tests for AmbiguityFieldGenerator — Contract #2: ambiguity is
mapped, not collapsed."""

from __future__ import annotations

from lae.config import LAEConfig
from lae.fields.ambiguity_field import AmbiguityFieldGenerator


def test_source_boundary_region_present(make_event):
    field = AmbiguityFieldGenerator().generate(make_event(source="origin"))
    boundary = field.region_by_id("region::origin::boundary")
    assert boundary is not None
    assert "source_boundary" in boundary.semantic_tags


def test_one_region_per_candidate(make_event):
    profile = {"a": 0.4, "b": 0.3, "c": 0.2}
    field = AmbiguityFieldGenerator().generate(make_event(profile=profile))
    for target in profile:
        assert field.region_by_id(f"region::{target}") is not None


def test_no_winner_selected(make_event):
    """The generator must never collapse ambiguity: every candidate
    keeps a region regardless of confidence ranking."""
    profile = {"strong": 0.9, "weak": 0.1}
    field = AmbiguityFieldGenerator().generate(make_event(profile=profile))
    assert field.region_by_id("region::strong") is not None
    assert field.region_by_id("region::weak") is not None


def test_voids_below_threshold(make_event):
    profile = {"a": 0.95, "tiny": 0.01}
    field = AmbiguityFieldGenerator().generate(make_event(profile=profile))
    assert "region::tiny" in field.voids


def test_coherence_islands_above_threshold(make_event):
    profile = {"dominant": 0.8, "minor": 0.2}
    field = AmbiguityFieldGenerator().generate(make_event(profile=profile))
    assert "region::dominant" in field.coherence_islands


def test_conflict_topology_links_close_candidates(make_event):
    profile = {"a": 0.35, "b": 0.33, "far": 0.05}
    field = AmbiguityFieldGenerator().generate(make_event(profile=profile))
    assert "region::b" in field.conflict_topology.get("region::a", [])
    assert "region::a" in field.conflict_topology.get("region::b", [])
    assert "region::far" not in field.conflict_topology.get("region::a", [])


def test_min_regions_padding(make_event):
    cfg = LAEConfig()
    field = AmbiguityFieldGenerator(cfg).generate(
        make_event(profile={"only": 1.0})
    )
    assert len(field.regions) >= cfg.min_regions
    pad = [r for r in field.regions if "unmapped" in r.semantic_tags]
    assert pad, "padding regions must be tagged unmapped"
    assert all(r.id in field.voids for r in pad)


def test_gradients_cover_all_candidates(make_event):
    profile = {"a": 0.4, "b": 0.3}
    field = AmbiguityFieldGenerator().generate(make_event(profile=profile))
    assert set(field.gradients) == {"region::a", "region::b"}
    assert all(v >= 0.0 for v in field.gradients.values())
