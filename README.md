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

# 🚀 Getting Started

```bash
# Install (editable, with test tooling)
pip install -e ".[dev]"

# Run the full demo — synthetic transitions end-to-end
python examples/demo.py

# Run the test suite
pytest
```

Minimal embedding:

```python
from lae import LAE

engine = LAE()
outcome = engine.observe({
    "state_id": "stable_narrative_v3",
    "hypotheses": {"frame_A": 0.31, "frame_B": 0.29, "frame_C": 0.28},
})

if outcome.activated:
    result = outcome.result
    print(result.intent.vector)        # directional pressure, not a decision
    print(result.identity.invariants)  # what held through the crossing
```

Multi-mind (Phase 4):

```python
engine = LAE(agents=["alpha", "beta"])
collective = engine.observe_collective({"alpha": obs_a, "beta": obs_b})
```

A presence across restarts (persistence):

```python
engine = LAE(persist_path="lae_state.json")
# wakes with every remembered crossing and the identity it had become;
# autosaves memory + identity after each activation
print(engine.restored)  # True if prior state was found and loaded
```

LAE has **zero hard dependencies** — the standard library is enough. `pyyaml` is optional (CONFIG.yaml loading), `pytest` is dev-only.

---

# 🧠 System Architecture

## 📦 Repository Map

```
Liminal-Anchor-Engine/
│
├── README.md / ARCHITECTURE.md / CONTRACTS.md / TYPES.md / CLAUDE.md
├── pyproject.toml
│
├── lae/
│   ├── __init__.py                # public API: LAE, LiminalAnchorEngine, core types
│   ├── CONFIG.yaml                # default runtime configuration
│   ├── config.py                  # typed config + YAML loader (optional dep)
│   ├── types.py                   # the six canonical dataclasses (mirrors schemas/)
│   ├── counters.py                # resumable monotonic ID counters
│   ├── persistence.py             # durable memory + identity (atomic JSON state file)
│   ├── pipeline.py                # LiminalAnchorEngine — the 6-layer pipeline
│   │
│   ├── detectors/
│   │   └── transition_detector.py # confidence collapse / conflict / oscillation rules
│   ├── fields/
│   │   └── ambiguity_field.py     # graph-model AmbiguityField generator
│   ├── anchors/
│   │   └── anchor_allocator.py    # continuity / stability / non-collapse / exploration
│   ├── memory/
│   │   ├── liminal_memory_buffer.py      # facade the pipeline talks to
│   │   ├── transition_episode_store.py
│   │   ├── ambiguity_signature_index.py  # cosine-similarity retrieval
│   │   ├── memory_retrieval.py
│   │   └── compression_strategy.py
│   ├── intent/
│   │   └── proto_intent_synthesizer.py
│   ├── identity/
│   │   ├── identity_gradient_mapper.py
│   │   ├── identity_field_model.py       # live gradient + crystallization guard
│   │   ├── invariance_tracker.py
│   │   ├── plasticity_analyzer.py
│   │   └── evolution_dynamics.py
│   ├── multimind/                 # Phase 4
│   │   ├── coordinator.py
│   │   ├── transition_merger.py
│   │   ├── shared_ambiguity_field.py
│   │   └── collective_intent.py
│   ├── routing/
│   │   └── event_router.py        # pub/sub event streaming
│   └── integration/               # Phase 5
│       ├── external_api.py        # LAE — the stable embedding surface
│       ├── system_hooks.py        # pre-transition veto / annotation hooks
│       └── diagnostics.py
│
├── schemas/                       # JSON Schemas — source of truth (Contract #0)
├── examples/
│   └── demo.py
└── tests/
    ├── unit/                      # pytest unit tests per layer
    ├── smoke/                     # Phase 1 end-to-end narrative suite
    └── integration/               # Phase 2–5 narrative suites
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

**→ See [`integration/README.md`](integration/README.md) for the full integration guide** —
what LAE is in depth, the input/output contract, and step-by-step wiring
(including how to feed a local LLM running in a terminal).

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

All five phases have a working implementation. Current focus: hardening, examples, and real-host integrations.

## Phase 0 — Structural Definition ✅

- [x] Define subsystem boundaries  
- [x] Establish repo map  
- [x] Define core abstractions  
- [x] Finalize type contracts (TYPES.md)  
- [x] Formalize event schemas (schemas/)  

---

## Phase 1 — Minimal Functional Skeleton ✅

- [x] Implement TransitionDetector (rule-based MVP)  
- [x] Basic AmbiguityField generator (graph model)  
- [x] Simple Anchor allocator (constraint tagging)  
- [x] In-memory LiminalMemoryBuffer  
- [x] Proto-intent heuristic generator  

Outcome: System can run synthetic transitions end-to-end

---

## Phase 2 — Structured Memory & Retrieval ✅

- [x] Embedding-based transition indexing  
- [x] Ambiguity signature clustering  
- [x] Historical transition retrieval  
- [x] Pattern-based anchor suggestion  

Outcome: System learns from transitions

---

## Phase 3 — Identity Gradient System ✅

- [x] IdentityGradientMapper implementation  
- [x] Track invariance vs plasticity  
- [x] Build evolution trajectory graphs  
- [x] Add identity drift forecasting  

Outcome: System can describe “becoming”

---

## Phase 4 — Multi-Agent / Multi-Mind Support ✅

- [x] Cross-model transition merging  
- [x] Conflict resolution across agents  
- [x] Shared ambiguity fields  
- [x] Collective proto-intent synthesis  

Outcome: Distributed cognition support

---

## Phase 5 — Production Integration Layer ✅

- [x] External API stabilization  
- [x] Hook-based integration system  
- [x] Event streaming architecture  
- [x] Observability + diagnostics layer  

Outcome: LAE usable as embedded subsystem in larger architectures

---

# 🧾 Closing Definition

The Liminal Anchor Engine is not a state machine.

It is a **transition machine**.

It does not ask:

“What are you?”

It asks:

“What happens to what you are while you are becoming something else?”
