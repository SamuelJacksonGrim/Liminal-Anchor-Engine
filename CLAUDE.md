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

**All five roadmap phases have a working implementation.** The project is now in a hardening / integration stage. The package is pure Python with **zero hard dependencies** (`pyyaml` optional, `pytest` dev-only) and installs with `pip install -e ".[dev]"`.

| Phase | Name | Status |
|---|---|---|
| 0 | Structural Definition | ✅ Done (docs + schemas) |
| 1 | Minimal Functional Skeleton | ✅ Done (`pipeline.py` end-to-end) |
| 2 | Structured Memory & Retrieval | ✅ Done (cosine-similarity retrieval, anchor suggestions) |
| 3 | Identity Gradient System | ✅ Done (`identity/` live gradient model) |
| 4 | Multi-Agent / Multi-Mind Support | ✅ Done (`multimind/`) |
| 5 | Production Integration Layer | ✅ Done (`integration/external_api.py`, hooks, events, diagnostics) |

---

## Repository Structure (actual)

The implemented tree intentionally deviates from the original planned map in older docs — it is flatter. Key deviations: orchestration lives in `lae/pipeline.py` (not a `core/` package), all canonical types live in `lae/types.py` (no `events/` package), the event router lives in `lae/routing/`, and detector rules are methods on one `TransitionDetector` class rather than separate modules.

```
Liminal-Anchor-Engine/
├── CLAUDE.md / README.md / ARCHITECTURE.md / CONTRACTS.md / TYPES.md
├── pyproject.toml                 # package: liminal-anchor-engine
│
├── lae/
│   ├── __init__.py                # public API: LAE, LiminalAnchorEngine, all core types
│   ├── CONFIG.yaml                # default runtime configuration
│   ├── config.py                  # LAEConfig + load_config (yaml optional, never raises)
│   ├── types.py                   # six canonical dataclasses + TimeWindow (mirror schemas/)
│   ├── pipeline.py                # LiminalAnchorEngine: detector → field → anchors → memory → intent → identity
│   ├── detectors/transition_detector.py
│   ├── fields/ambiguity_field.py
│   ├── anchors/anchor_allocator.py
│   ├── memory/                    # liminal_memory_buffer.py is the facade; pipeline talks only to it
│   ├── intent/proto_intent_synthesizer.py
│   ├── identity/                  # mapper + field model + invariance/plasticity/evolution trackers
│   ├── multimind/                 # Phase 4: coordinator, transition merger, shared field, collective intent
│   ├── routing/event_router.py    # pub/sub; subscriber exceptions are isolated
│   └── integration/               # Phase 5: external_api.py (class LAE), system_hooks.py, diagnostics.py
│
├── schemas/                       # JSON Schemas — structural source of truth (Contract #0)
├── examples/demo.py               # runnable end-to-end demo (also exercised by CI)
└── tests/
    ├── conftest.py                # make_event / make_field fixtures
    ├── unit/                      # pytest unit tests per layer
    ├── smoke/, integration/       # narrative check-suite scripts (exit non-zero on failure)
    └── test_suites.py             # pytest wrappers that run the narrative suites
```

---

## Core Design Contracts (Non-Negotiable)

Source: `CONTRACTS.md`. Every module must comply. A module that violates any contract is not part of LAE.

### 0. Schemas are the source of truth
`schemas/*.json` define structure; contracts define interpretation. The dataclasses in `lae/types.py` must match the schemas field-for-field — no renaming, no semantic expansion. `tests/unit/test_types.py` enforces this parity automatically.

### 1. Transitions are primary
Detectors identify *leaving states*, not states. Memory stores *crossings*, not snapshots. Identity tracks *drift*, not attributes.

### 2. Ambiguity must be structured
Every `AmbiguityField` carries regions, gradients, voids, coherence islands, and a conflict topology. The field generator never selects a winner.

### 3. Anchors are constraints, not states
Every `Anchor` specifies `protected_features`, `allowed_mutations`, `forbidden_mutations`, `priority`, `scope`. Note: `scope` is either a single region ID or a pipe-delimited pair (`"region::a|region::b"`) — always `split("|")` before comparing.

### 4. Intent begins as drift
`ProtoIntent` is directional pressure, never a decision. It carries causal history (`origin_episode_ids`) and source uncertainty (`ambiguity_lineage`). Stability reflects temporal coherence, not correctness.

### 5. Identity is a gradient field
`IdentityGradient` tracks invariants, plasticity zones, rigidity, drift vectors, and an append-only `trajectory_history`. Invariants are append-only; rigidity is clamped [0, 1]; the crystallization guard keeps at least one non-invariant feature plastic.

### 6. Prime directive
> Preserve continuity without preventing transformation.

---

## Key Runtime Facts

- **Observation contract** (input to `TransitionDetector.observe` / `LAE.observe`):
  ```python
  {"state_id": str, "hypotheses": {target_id: confidence}, "timestamp": float}  # timestamp optional
  ```
- **Trigger rules** (defaults from `lae/CONFIG.yaml`): confidence_collapse (top conf < 0.4), hypothesis_conflict (top two within 0.15), frame_oscillation (top hypothesis flips ≥2× inside a 1500 ms window — needs ≥3 observations).
- A confident switch (e.g. 0.91 vs 0.22) fires **nothing** — the engine staying dormant outside liminal states is correct behavior, not a bug.
- `LiminalAnchorEngine.process()` returns `None` when no trigger fires; `LAE.observe()` wraps this in `ObservationOutcome(activated=False)`.
- Event stream per activation, in order: `transition.detected`, `field.generated`, `anchors.allocated`, `episode.recorded`, `intent.synthesized`, `identity.updated`.
- ID conventions: regions `region::<name>` (source boundary: `region::<state>::boundary`), anchors `anchor::<kind>::NNNN`, episodes `episode::NNNNNN`. The anchor/episode counters are module-level and monotonically increase across engine instances within a process.
- Safety guards (config-controlled): `max_active_anchors` cap, `prevent_anchor_overconstraint` (at least one region stays unconstrained; exploration anchors with `allowed_mutations == ["*"]` don't count as constraining), `prevent_identity_crystallization` (rigidity ceiling 0.9 for non-invariants).
- `LAEConfig.raw` deep-copies `DEFAULTS` — config instances are isolated; never share nested dicts.

---

## Development Workflow

### Setup, run, test
```bash
pip install -e ".[dev]"
pytest                      # full suite: unit tests + wrapped narrative suites
python examples/demo.py     # end-to-end demo, runs without install too
```

### CI
`.github/workflows/ci.yml` runs `pytest` and the demo on Python 3.10–3.12 for pushes to `main` and all PRs.

### Git branches
- `main` — stable, protected
- `claude/<descriptor>` — AI-assisted feature/doc branches
- Create feature branches off `main`; merge via PR

### Commit message style
Imperative mood, capitalized verb, short subject (≤50 chars), optional detail body:
```
Add LAE TYPES documentation
Fix anchor overconstraint guard scope parsing
```

### Push
Always push with: `git push -u origin <branch-name>`

---

## AI Assistant Guidelines

**Before changing any module:**
1. Re-read `CONTRACTS.md` — check which invariants apply.
2. If a canonical type needs a new field: add it to the JSON schema in `schemas/` first, then `lae/types.py`, then `TYPES.md` and `CONTRACTS.md`. The schema-parity test will fail until all are aligned — that's by design.

**Types are canonical:**
The six types in `lae/types.py` are ground truth (with `schemas/` as the structural authority). Never create parallel or renamed versions of the same concept.

**Layer boundaries:**
The pipeline (`lae/pipeline.py`) is the only place layers are wired together; `lae/integration/external_api.py` (class `LAE`) is the only stable external surface. Memory submodules are private behind `LiminalMemoryBuffer`. Don't reach around the facades.

**Feedback loops are intentional:**
The system is not strictly feedforward (anchors reshape the field, identity adjusts anchor priorities, memory influences intent). When adding a feedback path, document it in a comment.

**Failure modes to avoid** (`ARCHITECTURE.md` §10):
- Over-collapsing ambiguity into a single resolution prematurely
- Over-constraining with too many anchors, preventing meaningful transition
- Hardening identity into a fixed point instead of maintaining a gradient
- Treating past transitions as deterministic templates in memory retrieval

**Tests:**
- Unit tests live in `tests/unit/test_<module>.py` using the `make_event` / `make_field` fixtures from `tests/conftest.py`.
- The narrative suites (`tests/smoke/`, `tests/integration/`) are runnable scripts that exit non-zero on failure; `tests/test_suites.py` wraps them for pytest. Keep both styles working.
- Every new module gets unit tests in the same change. Contract assertions (e.g. "intent binds no decision") belong in tests, not just docstrings.

**Do not:**
- Treat states as primary objects — transitions are always the unit of analysis
- Store only pre- or post-transition state in memory — always store the crossing
- Produce a `ProtoIntent` that encodes a committed decision
- Represent identity as a static dict or fixed attribute set
- Add hard runtime dependencies — the zero-dependency property is deliberate
