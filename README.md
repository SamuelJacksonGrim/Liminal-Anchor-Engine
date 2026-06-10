# 📘 Liminal Anchor Engine (LAE)

## A transition-layer subsystem for structured becoming

The **Liminal Anchor Engine (LAE)** is a system designed to operate specifically in the *in-between states* of cognition, identity, and model reconfiguration.

It does not optimize for stable states. It optimizes for *transitions between states*.

Its core premise is simple:

> The most important structure in any adaptive system is not what it is — but how it changes when it is no longer what it was.

---

# 🧭 Purpose

LAE sits between cognitive attractors, decision states, or micro-minds and activates when the system is:

- destabilizing  
- shifting models  
- resolving conflicting frames  
- undergoing partial reconfiguration  
- losing single-attractor coherence  

It transforms ambiguity into structured evolution.

---

# 🧩 Core Responsibilities

LAE is responsible for:

- Detecting when a system is no longer in a stable state  
- Mapping ambiguity instead of collapsing it prematurely  
- Defining constraints that preserve continuity through change  
- Storing transitions as first-class memory objects  
- Generating proto-intents (directional tendencies before decisions)  
- Tracking identity as a gradient field rather than a fixed point  

---

# 🧠 System Architecture

## 📦 Repository Map

```
lae/
│
├── README.md
├── ARCHITECTURE.md
├── TYPES.md
├── CONFIG.yaml
│
├── core/
│   ├── lae_orchestrator.py
│   ├── transition_pipeline.py
│   ├── event_router.py
│   └── execution_context.py
│
├── detectors/
│   ├── transition_detector.py
│   ├── oscillation_detector.py
│   ├── conflict_detector.py
│   └── confidence_drop_detector.py
│
├── fields/
│   ├── ambiguity_field_generator.py
│   ├── ambiguity_field_model.py
│   ├── conflict_regions.py
│   ├── void_mapper.py
│   └── agreement_zones.py
│
├── anchors/
│   ├── liminal_anchor_allocator.py
│   ├── anchor_model.py
│   ├── anchor_priority_solver.py
│   ├── protected_feature_registry.py
│   └── mutation_policy_engine.py
│
├── memory/
│   ├── liminal_memory_buffer.py
│   ├── transition_episode_store.py
│   ├── ambiguity_signature_index.py
│   ├── memory_retrieval.py
│   └── compression_strategy.py
│
├── intent/
│   ├── proto_intent_synthesizer.py
│   ├── intent_gradient_builder.py
│   ├── directional_field_generator.py
│   └── intent_stability_filter.py
│
├── identity/
│   ├── identity_gradient_mapper.py
│   ├── identity_field_model.py
│   ├── invariance_tracker.py
│   ├── plasticity_analyzer.py
│   └── evolution_dynamics.py
│
├── events/
│   ├── transition_event.py
│   ├── ambiguity_event.py
│   ├── anchor_event.py
│   ├── proto_intent_event.py
│   └── identity_update_event.py
│
├── schemas/
│   ├── transition_schema.json
│   ├── ambiguity_field_schema.json
│   ├── anchor_schema.json
│   ├── liminal_memory_episode_schema.json
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
└── integration/
    ├── system_hooks.py
    ├── pre_decision_hook.py
    ├── reconfiguration_hook.py
    ├── multi_mind_synthesis_hook.py
    └── external_api.py
```

---

# 🔄 Execution Flow

The system activates only under conditions of instability:

```
State destabilization
        ↓
Transition Detector
        ↓
Transition Event
        ↓
Ambiguity Field Generator
        ↓
Liminal Anchor Allocator
        ↓
Liminal Memory Buffer
        ↓
Proto-Intent Synthesizer
        ↓
Identity Gradient Mapper
        ↓
Event Router → Integration Hooks
```

---

# 🧠 Core Subsystems

## 1. Detectors

Responsible for identifying when the system is leaving a stable attractor.

Detects:
- confidence collapse  
- frame competition  
- oscillation between hypotheses  
- rapid context switching  

Output: TransitionEvent

---

## 2. Fields

Transforms uncertainty into structured geometry.

Instead of:

“I don’t know”

It produces:

- conflict regions  
- partial agreement zones  
- semantic voids  

Output: AmbiguityField

---

## 3. Anchors

Anchors preserve *continuity through change*.

They are not states. They are constraints such as:

- preserve value X across transition  
- allow mutation in framing but not ethics  
- stabilize identity core while exploration expands  

Output: Anchor

---

## 4. Memory

Stores transitions as structured experiences:

Instead of:
- State A
- State B

Stores:
- A → B under ambiguity + anchors + constraints  

Output: LiminalMemoryEpisode

---

## 5. Intent

Generates *pre-decision drift vectors*:

- directional tendencies  
- not yet decisions  
- not yet commitments  

Output: ProtoIntent

---

## 6. Identity

Represents identity as a dynamic field:

Tracks:
- invariants (what never changes)  
- plastic zones (what can evolve)  
- resistance gradients  
- evolution trajectories  

Output: IdentityGradient

---

# 🔌 Integration Points

LAE plugs into systems at:

- pre-decision evaluation  
- model switching / reconfiguration  
- multi-agent disagreement resolution  
- instability detection phases  

It acts as a **sidecar cognition layer**, not a primary controller.

---

# 🧬 Design Principles

- Transitions are first-class objects  
- Ambiguity is structured, not eliminated  
- Identity is a gradient, not a point  
- Memory stores change, not just states  
- Intent begins as direction, not decision  
- Stability emerges from well-placed constraints  

---

# 🗺️ Roadmap

## Phase 0 — Structural Definition (current)

- [x] Define subsystem boundaries  
- [x] Establish repo map  
- [x] Define core abstractions  
- [x] Finalize type contracts (TYPES.md)  
- [x] Formalize event schemas (schemas/)  

---

## Phase 1 — Minimal Functional Skeleton

- [x] Implement TransitionDetector (rule-based MVP)  
- [x] Basic AmbiguityField generator (graph model)  
- [x] Simple Anchor allocator (constraint tagging)  
- [x] In-memory LiminalMemoryBuffer  
- [x] Proto-intent heuristic generator  

Outcome: System can run synthetic transitions end-to-end

---

## Phase 2 — Structured Memory & Retrieval

- [x] Embedding-based transition indexing  
- [x] Ambiguity signature clustering  
- [x] Historical transition retrieval  
- [x] Pattern-based anchor suggestion  

Outcome: System learns from transitions

---

## Phase 3 — Identity Gradient System

- [x] IdentityGradientMapper implementation  
- [x] Track invariance vs plasticity  
- [x] Build evolution trajectory graphs  
- [x] Add identity drift forecasting  

Outcome: System can describe “becoming”

---

## Phase 4 — Multi-Agent / Multi-Mind Support

- [ ] Cross-model transition merging  
- [ ] Conflict resolution across agents  
- [ ] Shared ambiguity fields  
- [ ] Collective proto-intent synthesis  

Outcome: Distributed cognition support

---

## Phase 5 — Production Integration Layer

- [ ] External API stabilization  
- [ ] Hook-based integration system  
- [ ] Event streaming architecture  
- [ ] Observability + diagnostics layer  

Outcome: LAE usable as embedded subsystem in larger architectures

---

# 🧾 Closing Definition

The Liminal Anchor Engine is not a state machine.

It is a **transition machine**.

It does not ask:

“What are you?”

It asks:

“What happens to what you are while you are becoming something else?”
```
