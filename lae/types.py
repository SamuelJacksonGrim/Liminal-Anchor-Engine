"""
lae.types — Canonical core data structures.

Source of truth: schemas/ (per Contract #0).
These dataclasses mirror TYPES.md and the JSON schemas exactly.
No field renaming. No semantic expansion.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class TimeWindow:
    start: float
    end: float

    def duration(self) -> float:
        return self.end - self.start


@dataclass
class TransitionEvent:
    """Contract #1 — Represents only detected transition boundaries.

    Does not include interpretation logic. Confidence values are
    scalar probabilities per hypothesis.
    """

    source_state_id: str
    candidate_target_states: list[str]
    confidence_profile: dict[str, float]
    conflict_score: float
    time_window: TimeWindow


@dataclass
class Region:
    """Atomic partition of uncertainty space (Contract #2)."""

    id: str
    conflict_density: float
    coherence_score: float
    semantic_tags: list[str]
    neighbors: list[str]


@dataclass
class AmbiguityField:
    """Contract #2 — Ambiguity is mapped, not collapsed.

    - voids: region IDs with no valid model coverage
    - coherence_islands: region IDs with high local coherence
    - conflict_topology: adjacency map of conflict relationships
    - gradients: directional uncertainty pressure across the field
    """

    regions: list[Region]
    voids: list[str] = field(default_factory=list)
    coherence_islands: list[str] = field(default_factory=list)
    conflict_topology: dict[str, list[str]] = field(default_factory=dict)
    gradients: dict[str, float] = field(default_factory=dict)

    def region_by_id(self, region_id: str) -> Region | None:
        for r in self.regions:
            if r.id == region_id:
                return r
        return None


@dataclass
class Anchor:
    """Contract #3 — Anchors are constraints only. They do not encode state.

    Priority is relative ordering only (higher = stronger constraint).
    """

    anchor_id: str
    protected_features: list[str]
    allowed_mutations: list[str]
    forbidden_mutations: list[str]
    priority: int
    scope: str


@dataclass
class LiminalMemoryEpisode:
    """Contract #4 — Stores transition trace, not state snapshots.

    - ambiguity_signature is opaque (schema-defined only)
    - identity_shift_delta is a diff object, not a full state
    """

    episode_id: str
    source_state_id: str
    target_state_ids: list[str]
    anchors_used: list[str]
    ambiguity_signature: dict[str, Any]
    identity_shift_delta: dict[str, Any]


@dataclass
class ProtoIntent:
    """Contract #5 — Directional only (no decision binding).

    - magnitude is scalar intensity of vector field
    - stability_score reflects temporal coherence, not correctness
    """

    vector: dict[str, float]
    magnitude: float
    stability_score: float
    origin_episode_ids: list[str]
    ambiguity_lineage: list[str]


@dataclass
class IdentityGradient:
    """Contract #6 — Identity is a field, not a vector.

    - invariants: features that must remain unchanged across all transitions
    - rigidity: resistance weighting per dimension
    - plasticity_zones: high-change regions
    - trajectory_history: append-only
    """

    invariants: list[str]
    direction: dict[str, float]
    rigidity: dict[str, float]
    plasticity_zones: list[str]
    drift_vectors: dict[str, float]
    trajectory_history: list[dict[str, Any]] = field(default_factory=list)
