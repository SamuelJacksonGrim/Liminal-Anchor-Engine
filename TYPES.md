# LAE TYPES

---

## TransitionEvent

- source_state_id: str
- candidate_target_states: list[str]
- confidence_profile: dict[str, float]
- conflict_score: float
- time_window: {start: float, end: float}

---

## AmbiguityField

- regions: list[Region]
- voids: list[str]
- coherence_islands: list[str]
- conflict_topology: dict[str, list[str]]
- gradients: dict[str, float]

Region:
- id: str
- conflict_density: float
- coherence_score: float
- semantic_tags: list[str]
- neighbors: list[str]

---

## Anchor

- anchor_id: str
- protected_features: list[str]
- allowed_mutations: list[str]
- forbidden_mutations: list[str]
- priority: int
- scope: str

---

## LiminalMemoryEpisode

- episode_id: str
- source_state_id: str
- target_state_ids: list[str]
- anchors_used: list[str]
- ambiguity_signature: dict
- identity_shift_delta: dict

---

## ProtoIntent

- vector: dict[str, float]
- magnitude: float
- stability_score: float
- origin_episode_ids: list[str]
- ambiguity_lineage: list[str]

---

## IdentityGradient

- invariants: list[str]
- direction: dict[str, float]
- rigidity: dict[str, float]
- plasticity_zones: list[str]
- drift_vectors: dict[str, float]
- trajectory_history: list[dict]
