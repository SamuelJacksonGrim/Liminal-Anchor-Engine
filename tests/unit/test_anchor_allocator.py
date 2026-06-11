"""Unit tests for AnchorAllocator — Contract #3: anchors are constraints,
not states."""

from __future__ import annotations

from lae.anchors.anchor_allocator import AnchorAllocator
from lae.config import LAEConfig
from lae.types import AmbiguityField, Region


def test_continuity_anchor_on_source_boundary(make_field):
    field = make_field(source="origin")
    anchors = AnchorAllocator().allocate(field)
    continuity = [a for a in anchors if "continuity" in a.anchor_id]
    assert len(continuity) == 1
    assert continuity[0].priority == 100
    assert "region::origin::boundary" in continuity[0].protected_features


def test_non_collapse_anchor_per_conflict_pair(make_field):
    field = make_field(profile={"a": 0.35, "b": 0.33, "c": 0.30})
    anchors = AnchorAllocator().allocate(field)
    non_collapse = [a for a in anchors if "non_collapse" in a.anchor_id]
    # Each conflicting pair gets exactly one anchor (no duplicates for
    # both directions of the topology edge).
    edge_count = sum(len(v) for v in field.conflict_topology.values()) // 2
    assert len(non_collapse) <= edge_count
    scopes = [a.scope for a in non_collapse]
    assert len(scopes) == len(set(scopes))


def test_exploration_anchors_on_voids(make_field):
    field = make_field(profile={"a": 0.95, "tiny": 0.01})
    anchors = AnchorAllocator().allocate(field)
    exploration = [a for a in anchors if "exploration" in a.anchor_id]
    assert any(a.scope == "region::tiny" for a in exploration)
    for a in exploration:
        assert a.allowed_mutations == ["*"]
        assert "void_erasure" in a.forbidden_mutations


def test_max_active_anchors_cap(make_field):
    cfg = LAEConfig()
    cfg.raw["anchors"]["max_active_anchors"] = 2
    field = make_field(profile={"a": 0.35, "b": 0.33, "c": 0.30})
    anchors = AnchorAllocator(cfg).allocate(field)
    assert len(anchors) <= 2
    # Highest-priority anchors survive truncation.
    assert anchors[0].priority >= anchors[-1].priority


def test_overconstraint_guard_releases_a_region():
    """Regression: when every region is anchored (including via
    pipe-delimited pair scopes), the lowest-priority anchor is dropped."""
    cfg = LAEConfig()
    regions = [
        Region(id=f"region::{n}", conflict_density=0.5, coherence_score=0.5,
               semantic_tags=tags, neighbors=[])
        for n, tags in [("src::boundary", ["source_boundary"]),
                        ("a", ["candidate"]), ("b", ["candidate"])]
    ]
    field = AmbiguityField(
        regions=regions,
        coherence_islands=["region::a", "region::b"],
        conflict_topology={"region::a": ["region::b"], "region::b": ["region::a"]},
    )
    anchors = AnchorAllocator(cfg).allocate(field)
    anchored: set[str] = set()
    for a in anchors:
        anchored.update(a.scope.split("|"))
    region_ids = {r.id for r in field.regions}
    assert not region_ids <= anchored, (
        "at least one region must remain unanchored (prevent_anchor_overconstraint)"
    )


def test_anchor_fields_complete(make_field):
    """Contract #3: every anchor specifies all five constraint fields."""
    anchors = AnchorAllocator().allocate(make_field())
    for a in anchors:
        assert a.anchor_id
        assert isinstance(a.protected_features, list)
        assert isinstance(a.allowed_mutations, list)
        assert isinstance(a.forbidden_mutations, list)
        assert isinstance(a.priority, int)
        assert isinstance(a.scope, str)
