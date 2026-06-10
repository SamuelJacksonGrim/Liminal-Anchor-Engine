"""
lae.fields.ambiguity_field — AmbiguityField generator (Phase 1, graph model).

Layer 2. Input: TransitionEvent. Output: AmbiguityField.

Contract #2: ambiguity is mapped, not collapsed. The generator never
selects a winner — it structures the uncertainty space so downstream
layers can navigate it.

Phase 1 graph model:
- One region per candidate target state, plus one region for the
  source boundary itself ("the place being left").
- conflict_density per region derives from how contested that
  candidate is against its nearest rival.
- coherence_score derives from the candidate's own confidence mass.
- Regions below the void threshold (no meaningful support) are voids.
- Regions above the island threshold are coherence islands.
- conflict_topology connects regions whose confidences are within
  the conflict band of each other (they compete for the same mass).
- gradients give per-region resolution pressure: how strongly the
  field "pulls" toward that region right now.
"""

from __future__ import annotations

from ..config import LAEConfig
from ..types import AmbiguityField, Region, TransitionEvent

VOID_THRESHOLD = 0.05
ISLAND_THRESHOLD = 0.55
CONFLICT_BAND = 0.15


class AmbiguityFieldGenerator:
    def __init__(self, config: LAEConfig | None = None) -> None:
        self.config = config or LAEConfig()

    def generate(self, event: TransitionEvent) -> AmbiguityField:
        profile = event.confidence_profile
        total = sum(profile.values()) or 1.0
        normalized = {k: v / total for k, v in profile.items()}

        regions: list[Region] = []
        voids: list[str] = []
        islands: list[str] = []
        topology: dict[str, list[str]] = {}
        gradients: dict[str, float] = {}

        # Source-boundary region — the state being left is itself a
        # region of the field (Contract: transitions are primary).
        source_region_id = f"region::{event.source_state_id}::boundary"
        regions.append(
            Region(
                id=source_region_id,
                conflict_density=event.conflict_score,
                coherence_score=1.0 - event.conflict_score,
                semantic_tags=["source_boundary", event.source_state_id],
                neighbors=[],
            )
        )

        # Candidate regions.
        for target, conf in normalized.items():
            rid = f"region::{target}"
            rival = max(
                (v for k, v in normalized.items() if k != target), default=0.0
            )
            conflict_density = max(0.0, 1.0 - abs(conf - rival))
            region = Region(
                id=rid,
                conflict_density=round(conflict_density, 4),
                coherence_score=round(conf, 4),
                semantic_tags=["candidate", target],
                neighbors=[source_region_id],
            )
            regions.append(region)
            regions[0].neighbors.append(rid)

            if self.config.include_voids and conf < VOID_THRESHOLD:
                voids.append(rid)
            if self.config.include_coherence_islands and conf > ISLAND_THRESHOLD:
                islands.append(rid)

            gradients[rid] = round(conf * (1.0 - event.conflict_score), 4)

        # Conflict topology: candidates within the band compete directly.
        if self.config.include_conflict_graph:
            cands = list(normalized.items())
            for i, (a, ca) in enumerate(cands):
                for b, cb in cands[i + 1 :]:
                    if abs(ca - cb) < CONFLICT_BAND:
                        ra, rb = f"region::{a}", f"region::{b}"
                        topology.setdefault(ra, []).append(rb)
                        topology.setdefault(rb, []).append(ra)
                        # Conflicting regions are also field-adjacent.
                        self._link(regions, ra, rb)

        # Pad to min_regions with explicit unknown-space voids. The
        # field must always acknowledge unmapped territory.
        while len(regions) < self.config.min_regions:
            pad_id = f"region::unmapped::{len(regions)}"
            regions.append(
                Region(
                    id=pad_id,
                    conflict_density=0.0,
                    coherence_score=0.0,
                    semantic_tags=["unmapped"],
                    neighbors=[source_region_id],
                )
            )
            if self.config.include_voids:
                voids.append(pad_id)

        return AmbiguityField(
            regions=regions,
            voids=voids,
            coherence_islands=islands,
            conflict_topology=topology,
            gradients=gradients,
        )

    @staticmethod
    def _link(regions: list[Region], rid_a: str, rid_b: str) -> None:
        for r in regions:
            if r.id == rid_a and rid_b not in r.neighbors:
                r.neighbors.append(rid_b)
            elif r.id == rid_b and rid_a not in r.neighbors:
                r.neighbors.append(rid_a)
