# LAE TYPES

---

## TransitionEvent

- sourcestateid: str
- candidatetargetstates: list[str]
- confidence_profile: dict[str, float]
- conflict_score: float
- time_window: {start: float, end: float}

---

## AmbiguityField

- regions: list[Region]

Region:
- id: str
- conflictdensity: float
- coherencescore: float
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
- sourcestateid: str
- targetstateids: list[str]
- anchors_used: list[str]
- ambiguity_signature: dict
- identityshiftdelta: dict

---

## ProtoIntent

- vector: dict[str, float]
- magnitude: float
- stability_score: float
- origin_episode_ids: list[str]
- ambiguity_lineage: list[str]

---

## IdentityGradient

- direction: dict[str, float]
- rigidity: dict[str, float]
- plasticity_zones: list[str]
- drift_vectors: dict[str, float]
- trajectory_history: list[dict]
