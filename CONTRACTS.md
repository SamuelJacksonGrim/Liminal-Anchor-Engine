# CONTRACTS.md
## Liminal Anchor Engine (LAE)

---

# 0. Contract Rule

All contracts in this system MUST match `schemas/` exactly.

- Schemas define structure
- Contracts define interpretation constraints
- No field may exist in Contracts that is not present in schemas
- No renaming allowed
- No extra semantic expansion allowed

---

# 1. TransitionEvent Contract

MUST MATCH: `transition_schema.json`

Fields:

- source_state_id: string
- candidate_target_states: string[]
- confidence_profile: map<string, float>
- conflict_score: float
- time_window: {start: float, end: float}

Rules:

- Represents only detected transition boundaries
- Does not include interpretation logic
- Confidence values are scalar probabilities per hypothesis

---

# 2. AmbiguityField Contract

MUST MATCH: `ambiguity_field_schema.json`

Fields:

- regions: Region[]
- voids: string[]
- coherence_islands: string[]
- conflict_topology: map<string, string[]>
- gradients: map<string, float>

Region:

- id: string
- conflict_density: float
- coherence_score: float
- semantic_tags: string[]
- neighbors: string[]

Rules:

- Regions are atomic partitions of uncertainty space
- voids are region IDs with no valid model coverage
- coherence_islands are region IDs with high local coherence
- conflict_topology is an adjacency map of conflict relationships between regions
- gradients represent directional uncertainty pressure across the field
- Ambiguity is mapped, not collapsed

---

# 3. Anchor Contract

MUST MATCH: `anchor_schema.json`

Fields:

- anchor_id: string
- protected_features: string[]
- allowed_mutations: string[]
- forbidden_mutations: string[]
- priority: int
- scope: string

Rules:

- Anchors are constraints only
- Anchors do not encode state
- Priority is relative ordering only (higher = stronger constraint)

---

# 4. LiminalMemoryEpisode Contract

MUST MATCH: `liminal_memory_episode_schema.json`

Fields:

- episode_id: string
- source_state_id: string
- target_state_ids: string[]
- anchors_used: string[]
- ambiguity_signature: object
- identity_shift_delta: object

Rules:

- Stores transition trace, not state snapshots
- ambiguity_signature is opaque (schema-defined only)
- identity_shift_delta is a diff object, not a full state

---

# 5. ProtoIntent Contract

MUST MATCH: `proto_intent_schema.json`

Fields:

- vector: map<string, float>
- magnitude: float
- stability_score: float
- origin_episode_ids: string[]
- ambiguity_lineage: string[]

Rules:

- ProtoIntent is directional only (no decision binding)
- magnitude is scalar intensity of vector field
- stability_score reflects temporal coherence, not correctness

---

# 6. IdentityGradient Contract

MUST MATCH: `identity_gradient_schema.json`

Fields:

- invariants: string[]
- direction: map<string, float>
- rigidity: map<string, float>
- plasticity_zones: string[]
- drift_vectors: map<string, float>
- trajectory_history: object[]

Rules:

- Identity is a field, not a vector
- invariants are features that must remain unchanged across all transitions
- direction encodes the current gradient orientation of identity evolution
- rigidity represents resistance weighting per dimension
- plasticity_zones define high-change regions
- trajectory_history is append-only

---

# 7. Global Enforcement Rules

## 7.1 No Schema Drift
If schema changes, contract MUST be updated immediately.

## 7.2 No Semantic Expansion
Contracts may NOT add meaning beyond schema fields.

## 7.3 Computation Lives Elsewhere
Any derived logic belongs in:
- core/
- intent/
- identity/
NOT in contracts.

## 7.4 Contracts are Invariants Only
They define:
- structure
- constraints
- interpretation boundaries

NOT:
- algorithms
- heuristics
- behavior

---

# 8. System Guarantee

If all contracts match schemas exactly:

> LAE becomes structurally deterministic across all layers.
