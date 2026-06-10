# CLAUDE.md — Liminal Anchor Engine (LAE)

This file is the primary reference for AI assistants working in this repository.
Read it before making any design or implementation decisions.

---

## Project Overview

The **Liminal Anchor Engine (LAE)** is a transition-layer subsystem for adaptive cognitive systems. It activates exclusively when a system is *between* stable states — during model conflict, identity drift, confidence collapse, or frame competition.

The central inversion that defines the entire architecture:

> Traditional systems treat transitions as noise between states.
> LAE treats states as temporary stabilizations inside transitions.

LAE does not resolve ambiguity. It structures ambiguity into a navigable space, applies continuity constraints (anchors), stores the transition as a first-class memory object, extracts pre-decisional directional pressure (proto-intent), and updates the system's identity gradient.

LAE is a **sidecar cognition layer**, not a primary controller.

---

## Repository Status

**Current phase: Phase 0 — Structural Definition**

No implementation code exists yet. The repository contains only design documents:

| File | Purpose |
|---|---|
| `README.md` | Project overview, repository map, execution flow, roadmap |
| `ARCHITECTURE.md` | Layer descriptions, execution model, feedback dynamics, failure modes |
| `CONTRACTS.md` | 7 invariant rules every module must obey |
| `TYPES.md` | Canonical type definitions for all core data structures |
| `LICENSE` | Apache License 2.0 |

### Roadmap Summary

| Phase | Name | Status |
|---|---|---|
| 0 | Structural Definition | In progress (docs done, schemas pending) |
| 1 | Minimal Functional Skeleton | Not started |
| 2 | Structured Memory & Retrieval | Not started |
| 3 | Identity Gradient System | Not started |
| 4 | Multi-Agent / Multi-Mind Support | Not started |
| 5 | Production Integration Layer | Not started |

---

## Repository Structure

### Current files

```
Liminal-Anchor-Engine/
├── CLAUDE.md           ← this file
├── README.md
├── ARCHITECTURE.md
├── CONTRACTS.md
├── TYPES.md
└── LICENSE
```

### Planned `lae/` source tree (from README.md)

```
lae/
├── CONFIG.yaml
│
├── core/                          # Orchestration & pipeline coordination
│   ├── lae_orchestrator.py        # Main entry point; manages lifecycle
│   ├── transition_pipeline.py     # Executes the 6-layer pipeline
│   ├── event_router.py            # Routes events between layers
│   └── execution_context.py      # Holds per-activation state
│
├── detectors/                     # Identify when system leaves stable attractor
│   ├── transition_detector.py
│   ├── oscillation_detector.py
│   ├── conflict_detector.py
│   └── confidence_drop_detector.py
│
├── fields/                        # Transform uncertainty into structured geometry
│   ├── ambiguity_field_generator.py
│   ├── ambiguity_field_model.py
│   ├── conflict_regions.py
│   ├── void_mapper.py
│   └── agreement_zones.py
│
├── anchors/                       # Continuity constraints during transformation
│   ├── liminal_anchor_allocator.py
│   ├── anchor_model.py
│   ├── anchor_priority_solver.py
│   ├── protected_feature_registry.py
│   └── mutation_policy_engine.py
│
├── memory/                        # Store transitions, not state snapshots
│   ├── liminal_memory_buffer.py   # In-memory buffer (Phase 1)
│   ├── transition_episode_store.py
│   ├── ambiguity_signature_index.py
│   ├── memory_retrieval.py
│   └── compression_strategy.py
│
├── intent/                        # Pre-decisional directional vectors
│   ├── proto_intent_synthesizer.py
│   ├── intent_gradient_builder.py
│   ├── directional_field_generator.py
│   └── intent_stability_filter.py
│
├── identity/                      # Identity as dynamic gradient field
│   ├── identity_gradient_mapper.py
│   ├── identity_field_model.py
│   ├── invariance_tracker.py
│   ├── plasticity_analyzer.py
│   └── evolution_dynamics.py
│
├── events/                        # Inter-layer event definitions
│   ├── transition_event.py
│   ├── ambiguity_event.py
│   ├── anchor_event.py
│   ├── proto_intent_event.py
│   └── identity_update_event.py
│
├── schemas/                       # JSON schemas for all core types
│   ├── transition_schema.json
│   ├── ambiguity_field_schema.json
│   ├── anchor_schema.json
│   ├── memory_episode_schema.json
│   ├── proto_intent_schema.json
│   └── identity_gradient_schema.json
│
├── utils/
│   ├── similarity.py
│   ├── clustering.py
│   ├── graph_utils.py
│   ├── statistical_signals.py
│   └── time_windowing.py
│
└── integration/                   # Hooks into external systems (Phase 5)
    ├── system_hooks.py
    ├── pre_decision_hook.py
    ├── reconfiguration_hook.py
    ├── multi_mind_synthesis_hook.py
    └── external_api.py
```

---

## Core Design Contracts (Non-Negotiable)

Source: `CONTRACTS.md`. Every module must comply with all seven rules. A module that violates any contract is not part of LAE.

### 1. Transitions are primary
All computation is transition-centric. Detectors identify *leaving states*, not states. Memory stores *crossings*, not snapshots. Identity tracks *drift*, not attributes.
> States are temporary compressions of transition fields.

### 2. Ambiguity must be structured
Ambiguity is a navigable space, not noise. Every `AmbiguityField` must contain regions, gradients, voids, coherence islands, and a conflict topology. Unstructured ambiguity is invalid output.

### 3. Anchors are constraints, not states
Every `Anchor` must specify `protected_features`, `allowed_mutations`, `forbidden_mutations`, `priority`, and `temporal_scope`. Anchors preserve identity continuity without freezing identity.

### 4. Intent begins as drift
`ProtoIntent` is not a decision. It is directional pressure emerging from the ambiguity field before any choice is made. It must carry causal history (`origin_episode_ids`) and source uncertainty (`ambiguity_lineage`).

### 5. Identity is a gradient field
`IdentityGradient` is a dynamic manifold: invariants, plasticity zones, rigidity map, drift vectors, and trajectory history. It is never a fixed vector or a snapshot.

### 6. Prime directive
> Preserve continuity without preventing transformation.

This is the single global constraint that overrides all local optimizations.

### 7. System validity condition
A system state is valid only when: transitions are first-class objects; ambiguity is structured; anchors preserve invariants without freezing dynamics; proto-intents are non-decisional; identity is gradient-based.

---

## Data Types Reference

Source: `TYPES.md`. These are canonical. Extend them; do not redefine or replace them.

```python
from dataclasses import dataclass, field
from typing import Any

@dataclass
class TransitionEvent:
    source_state_id: str
    candidate_target_states: list[str]
    confidence_profile: dict[str, float]
    conflict_score: float
    time_window: dict[str, float]          # {"start": float, "end": float}

@dataclass
class Region:
    id: str
    conflict_density: float
    coherence_score: float
    semantic_tags: list[str]
    neighbors: list[str]

@dataclass
class AmbiguityField:
    regions: list[Region]

@dataclass
class Anchor:
    anchor_id: str
    protected_features: list[str]
    allowed_mutations: list[str]
    forbidden_mutations: list[str]
    priority: int
    scope: str

@dataclass
class LiminalMemoryEpisode:
    episode_id: str
    source_state_id: str
    target_state_ids: list[str]
    anchors_used: list[str]
    ambiguity_signature: dict[str, Any]
    identity_shift_delta: dict[str, Any]

@dataclass
class ProtoIntent:
    vector: dict[str, float]
    magnitude: float
    stability_score: float
    origin_episode_ids: list[str]
    ambiguity_lineage: list[str]

@dataclass
class IdentityGradient:
    direction: dict[str, float]
    rigidity: dict[str, float]
    plasticity_zones: list[str]
    drift_vectors: dict[str, float]
    trajectory_history: list[dict[str, Any]]
```

---

## Architecture Layers

Source: `ARCHITECTURE.md` sections 6.1–6.6.

### Layer 1 — Detection (`detectors/`)
**Input:** raw cognitive signals (confidence scores, hypothesis overlap, contradiction density, temporal oscillation)
**Output:** `TransitionEvent`
**Trigger condition:** confidence collapse below threshold, oscillation between hypotheses, unresolved frame conflict, rapid context switching, model reconfiguration request.
The `TransitionEvent` is the atomic trigger for all downstream layers.

### Layer 2 — Ambiguity Field (`fields/`)
**Input:** `TransitionEvent`
**Output:** `AmbiguityField`
Maps uncertainty into structured geometry: high-conflict regions, consensus zones, semantic voids. The field becomes the operating space for all downstream layers. Uncertainty is mapped, not removed.

### Layer 3 — Anchor (`anchors/`)
**Input:** `AmbiguityField` + identity/ethics/stability context
**Output:** `Anchor` set
Anchors are injected into the ambiguity field to reshape its topology and carve allowed paths of becoming. They define what must remain invariant, what may transform, and what is explicitly unconstrained. Anchor placement can feed back and modify the ambiguity field.

### Layer 4 — Memory (`memory/`)
**Input:** `AmbiguityField` + `Anchor` set
**Output:** `LiminalMemoryEpisode`
Encodes the A→B transition path with ambiguity structure, anchors applied, resolution pressure trajectory, and identity drift signature. Does NOT store state A or state B in isolation. In Phase 2, enables embedding-based retrieval of similar past transitions.

### Layer 5 — Intent (`intent/`)
**Input:** stabilized transition field + memory context
**Output:** `ProtoIntent`
Extracts directional gradients from the transition field. These are pre-decisional vector forces — directional tendencies that bias but do not determine future cognition. Proto-intents can re-weight ambiguity regions (feedback).

### Layer 6 — Identity (`identity/`)
**Input:** `ProtoIntent` + prior `IdentityGradient`
**Output:** updated `IdentityGradient`
Updates the system's self-model after each transition cycle. Tracks invariants, plastic regions, resistance boundaries, and drift vectors. Identity drift can feed back to adjust anchor priorities.

---

## Execution Flow

LAE runs in **event-triggered bursts**, not a continuous loop. It activates only under instability.

```
State destabilization detected
        ↓
Transition Detector  →  TransitionEvent
        ↓
Ambiguity Field Generator  →  AmbiguityField
        ↓
Liminal Anchor Allocator  →  Anchor set
        ↓
Liminal Memory Buffer  →  LiminalMemoryEpisode
        ↓
Proto-Intent Synthesizer  →  ProtoIntent
        ↓
Identity Gradient Mapper  →  IdentityGradient (updated)
        ↓
Event Router  →  Integration Hooks
```

This is a **feedback-linked transformation chain**, not a strict pipeline:
- Anchor placement can modify ambiguity field topology
- Identity drift can adjust anchor priorities
- Proto-intents can re-weight ambiguity regions
- Memory retrieval can influence detector sensitivity

---

## Planned Tech Stack

- **Language:** Python 3.x (inferred from all `.py` filenames in the planned structure)
- **License:** Apache 2.0
- **Phase 2 storage:** embedding-based vector index for transition memory retrieval
- **Build tooling:** none defined yet; add `pyproject.toml` when Phase 1 begins
- **Testing:** `pytest` is the natural fit; add alongside each module
- **CI/CD:** not configured yet; planned for Phase 5

---

## Development Workflow

### Git branches
- `main` — stable, protected
- `claude/<descriptor>` — AI-assisted feature/doc branches (current: `claude/claude-md-docs-z9us4m`)
- Create feature branches off `main`; merge via PR

### Commit message style
Observed pattern from git history:
```
Add LAE TYPES documentation
Add Internal Logic Contract for Liminal Anchor Engine
Add architecture documentation for Liminal Anchor Engine
Initialize README.md with project overview and details
```
Rules:
- Imperative mood, capitalized verb ("Add", "Implement", "Update", "Fix")
- Short subject line (50 chars or less)
- Follow with a blank line and a detail body when the change needs explanation

### Push
Always push with: `git push -u origin <branch-name>`

---

## AI Assistant Guidelines

Follow these rules when implementing any part of this system.

**Before writing any module:**
1. Re-read `CONTRACTS.md` — check which invariants apply to the module you are about to write.
2. Confirm the module's output type is one of the six canonical types in `TYPES.md` (or a clearly marked extension of one).

**Implementation order:**
Follow the roadmap phases in sequence. Phase 1 before Phase 2, etc. Within Phase 1, implement layers in pipeline order: `detectors/` → `fields/` → `anchors/` → `memory/` → `intent/` (identity comes in Phase 3).

**Layer decoupling:**
Layers communicate exclusively through the event types defined in `events/`. No direct cross-layer function calls. The `core/event_router.py` is the only cross-layer coupling point.

**Types are canonical:**
The six types in `TYPES.md` (and the dataclasses above) are the ground truth. If a new field is needed, add it to the existing type. Do not create parallel or renamed versions of the same concept.

**Feedback loops are intentional:**
The system is not strictly feedforward. Designing a layer to emit feedback events that influence earlier layers is correct behavior — but document the feedback path in a comment when adding one.

**Failure modes to avoid** (from `ARCHITECTURE.md` section 10):
- Over-collapsing ambiguity into a single resolution prematurely
- Over-constraining with too many anchors, preventing meaningful transition
- Hardening identity into a fixed point instead of maintaining a gradient
- Treating past transitions as deterministic templates in memory retrieval

**Tests:**
Write unit tests alongside each new module under a `tests/` directory mirroring the source tree (e.g., `tests/detectors/test_transition_detector.py`). Each test should exercise the module with a synthetic `TransitionEvent` and assert the output matches the canonical type contract.

**Do not:**
- Treat states as primary objects — transitions are always the unit of analysis
- Store only pre- or post-transition state in memory — always store the crossing
- Produce a `ProtoIntent` that encodes a committed decision
- Represent identity as a static dict or fixed attribute set
