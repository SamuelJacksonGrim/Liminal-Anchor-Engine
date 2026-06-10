"""
lae.anchors.anchor_allocator — Simple Anchor allocator (Phase 1, constraint tagging).

Layer 3. Input: AmbiguityField. Output: list[Anchor].

Contract #3: anchors are constraints only. They never encode state and
never select outcomes. They mark what must NOT change while the field
remains unresolved.

Phase 1 allocation rules:
- Source-boundary region always gets a continuity anchor (the system
  must remember where it is leaving from). Highest priority under
  priority_bias=identity_stability.
- Each coherence island gets a stability anchor protecting its
  coherent structure from premature mutation.
- Each high-conflict pair in the topology gets a non-collapse anchor:
  the conflict itself is protected from being resolved by fiat.
- Voids get exploration anchors permitting mutation (everything is an
  allowed mutation in unmapped space) but protecting the record that
  the void exists.

Safety (from CONFIG.yaml):
- max_active_anchors enforced by priority-ranked truncation
- prevent_anchor_overconstraint: at least one region must always remain
  fully mutable; if every region ends up anchored, the lowest-priority
  anchor is dropped.
"""

from __future__ import annotations

import itertools

from ..config import LAEConfig
from ..types import AmbiguityField, Anchor

_anchor_counter = itertools.count(1)


class AnchorAllocator:
    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()

    def allocate(self, field: AmbiguityField) -> list[Anchor]:
        anchors: list[Anchor] = []

        # 1. Continuity anchor on the source boundary.
        for region in field.regions:
            if "source_boundary" in region.semantic_tags:
                anchors.append(
                    Anchor(
                        anchor_id=self._next_id("continuity"),
                        protected_features=[region.id, "transition_origin"],
                        allowed_mutations=["confidence_profile"],
                        forbidden_mutations=["source_state_id", "region_removal"],
                        priority=100,
                        scope=region.id,
                    )
                )

        # 2. Stability anchors on coherence islands.
        for rid in field.coherence_islands:
            anchors.append(
                Anchor(
                    anchor_id=self._next_id("stability"),
                    protected_features=[rid, "coherence_score"],
                    allowed_mutations=["semantic_tags", "neighbors"],
                    forbidden_mutations=["region_removal", "coherence_inversion"],
                    priority=80,
                    scope=rid,
                )
            )

        # 3. Non-collapse anchors on conflict pairs.
        seen_pairs: set[frozenset[str]] = set()
        for rid, rivals in field.conflict_topology.items():
            for rival in rivals:
                pair = frozenset((rid, rival))
                if pair in seen_pairs:
                    continue
                seen_pairs.add(pair)
                anchors.append(
                    Anchor(
                        anchor_id=self._next_id("non_collapse"),
                        protected_features=sorted(pair) + ["conflict_edge"],
                        allowed_mutations=["conflict_density", "gradients"],
                        forbidden_mutations=["forced_resolution", "edge_removal"],
                        priority=60,
                        scope="|".join(sorted(pair)),
                    )
                )

        # 4. Exploration anchors on voids.
        for rid in field.voids:
            anchors.append(
                Anchor(
                    anchor_id=self._next_id("exploration"),
                    protected_features=["void_record"],
                    allowed_mutations=["*"],
                    forbidden_mutations=["void_erasure"],
                    priority=20,
                    scope=rid,
                )
            )

        # Safety: cap active anchors, priority-ranked.
        anchors.sort(key=lambda a: a.priority, reverse=True)
        anchors = anchors[: self.config.max_active_anchors]

        # Safety: prevent over-constraint — at least one region of the
        # field must remain fully unanchored and mutable.
        if self.config.prevent_anchor_overconstraint:
            anchored_scopes = {a.scope for a in anchors}
            all_region_ids = {r.id for r in field.regions}
            fully_covered = all(
                any(rid in scope for scope in anchored_scopes)
                for rid in all_region_ids
            )
            if fully_covered and anchors:
                anchors.pop()  # drop lowest-priority anchor

        return anchors

    @staticmethod
    def _next_id(kind: str) -> str:
        return f"anchor::{kind}::{next(_anchor_counter):04d}"
