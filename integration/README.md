# Integrating the Liminal Anchor Engine

> A deeper guide than the top-level README: what LAE actually is, what it does
> on each call, and exactly how to wire it into a host system — including a
> local LLM running in a terminal.

This folder is **documentation**. The integration *code* (the stable API,
hooks, diagnostics) lives in the Python package at [`../lae/integration/`](../lae/integration/),
and a working reference adapter lives at
[`../examples/rfe_integration.py`](../examples/rfe_integration.py).

---

## 1. What LAE is (and what it is not)

LAE is a **cognitive sidecar** — an organ you attach to a thinking system, not
an instrument you point at one.

- It is **not a measurement tool.** It does not score, rank, or evaluate a
  model. (The only measurement tools in this repo are the benchmarks in
  `examples/benchmark_overhead.py`, which measure *LAE's own* runtime cost.)
- It is **not a controller.** It never makes a decision or steers the host. It
  emits *directional pressure* (proto-intent) that the host is free to use or
  ignore.
- It **is** a transition-layer: it wakes up only when the host is *between*
  stable states — model conflict, confidence collapse, oscillation between
  framings — and turns that turbulence into navigable structure.

The defining inversion:

> Traditional systems treat transitions as noise between states.
> LAE treats states as temporary stabilizations inside transitions.

## 2. What it does on each call

You feed LAE one **observation** — a snapshot of "what the host currently
believes it might be doing." LAE checks whether that observation represents a
liminal moment. If not, it stays dormant (this is correct, not a bug). If it
does, it runs a six-stage pipeline and returns the result:

| Stage | Produces | Meaning |
|---|---|---|
| Detect | `TransitionEvent` | which state is being *left*, and why |
| Field | `AmbiguityField` | the uncertainty mapped into regions/voids/conflict topology — never collapsed to a winner |
| Anchor | `Anchor[]` | continuity constraints (what must be preserved through the change) |
| Memory | `LiminalMemoryEpisode` | the crossing stored as a first-class memory |
| Intent | `ProtoIntent` | pre-decisional directional pressure (advisory) |
| Identity | `IdentityGradient` | the system's drift, updated |

## 3. The integration contract

This is the seam. Everything else is yours to design.

**Input — the observation dict:**

```python
{
    "state_id": str,                    # what the system currently is / is doing
    "hypotheses": {target_id: confidence},  # competing next-states, confidence in [0,1]
    "timestamp": float,                 # optional; any monotonic clock (real or "ticks")
}
```

**Output — `ObservationOutcome`:**

```python
outcome.activated          # bool — did a transition fire?
outcome.vetoed             # bool — did a pre_transition hook block it?
outcome.result             # LiminalResult | None
outcome.result.event       # TransitionEvent
outcome.result.field       # AmbiguityField
outcome.result.anchors     # list[Anchor]
outcome.result.intent      # ProtoIntent  (advisory pressure)
outcome.result.identity    # IdentityGradient
outcome.result.episode     # LiminalMemoryEpisode
outcome.result.anchor_suggestions  # hints drawn from similar past crossings
outcome.host_annotations   # whatever your pre_resolution hooks attached
```

**When LAE fires** (defaults from `lae/CONFIG.yaml`):

- `confidence_collapse` — top confidence `< 0.4` (no clear winner)
- `hypothesis_conflict` — top two within `0.15` of each other
- `frame_oscillation` — top hypothesis flips ≥2× inside a 1500 ms window
  (needs ≥3 observations)

A confident switch (e.g. `0.91` vs `0.09`) fires **nothing**. Dormancy outside
liminal states is the design.

## 4. Wiring it in — the minimum

```python
from lae import LAE

lae = LAE()  # zero config, zero dependencies

# ...inside your host loop, once per step:
outcome = lae.observe({
    "state_id": current_state,
    "hypotheses": candidate_next_states,   # {id: confidence}
    "timestamp": step_clock,
})

if outcome.activated:
    pressure = outcome.result.intent.vector          # advisory direction
    keep     = [a.protected_features for a in outcome.result.anchors]
    # Use them as hints. LAE does not expect you to obey them.
```

That is the whole required surface. The sections below are optional power.

## 5. The real work: designing the signal

LAE can't read your host's mind — **you decide what counts as a hypothesis and
a confidence.** This is the one design decision that is genuinely yours, and it
is why LAE ships no built-in connector for any specific host. The reference
adapter ([`examples/rfe_integration.py`](../examples/rfe_integration.py)) maps
an RFE-Core2 rhythm router into the contract; yours will map something else.

### Wiring a local LLM running in a terminal

An LLM does not natively emit `{state_id, hypotheses, timestamp}`. You write a
thin adapter that derives them. Common signal sources, from least to most
invasive:

- **Multi-sample disagreement (model-agnostic).** Sample the model *n* times
  for the same prompt. Treat distinct answers as `hypotheses`, each one's
  frequency (or a normalized score) as its confidence. Wide disagreement →
  `confidence_collapse` / `hypothesis_conflict` fires.

  ```python
  answers = [llm(prompt) for _ in range(8)]
  counts = collections.Counter(normalize(a) for a in answers)
  total = sum(counts.values())
  outcome = lae.observe({
      "state_id": f"task::{task_id}",
      "hypotheses": {ans: n / total for ans, n in counts.items()},
      "timestamp": time.time(),
  })
  ```

- **Token logprobs (needs a backend that exposes them — llama.cpp, some Ollama
  setups).** Use the next-token (or candidate-completion) probabilities
  directly as `hypotheses`. Cheapest signal if your runtime gives it to you.

- **Multi-prompt / multi-persona (model-agnostic).** Ask the same question
  under different framings; the spread of answers becomes the hypotheses.

Whatever you pick, call `observe()` once per decision point and log the
returned `ProtoIntent` as advisory. **LAE never picks the answer for you** —
it structures the moment of indecision so the host can navigate it.

## 6. Optional power

**Hooks** (filter and annotate, never mutate engine internals):

```python
lae.hooks.on_pre_transition(lambda obs: obs["state_id"] != "ignore_me")  # veto-capable
lae.hooks.on_pre_resolution(lambda payload: {"host": "my-app"})          # annotate
```

**Events** (per-activation stream, in order): `transition.detected`,
`field.generated`, `anchors.allocated`, `episode.recorded`,
`intent.synthesized`, `identity.updated`.

```python
lae.events.subscribe("intent.synthesized", my_handler)
```

**Host-injected reconfiguration** (the one trigger LAE can't see from inside):

```python
lae.reconfigure({"reason": "model_swapped", "from": "7b", "to": "70b"})
```

**Persistence** (a presence that survives restarts):

```python
lae = LAE(persist_path="lae_state.json")  # restores memory + identity on init
# autosaves after each activation; lae.restored tells you if a file was found
```

**Multi-mind** (a roster of agents crossing together):

```python
lae = LAE(agents=["claude", "gpt", "gemini"])
result = lae.observe_collective({"claude": obs1, "gpt": obs2})
```

**Diagnostics** (observability):

```python
lae.diagnostics.snapshot()  # activation counts, health
```

## 7. Common pitfalls

- **Expecting it to answer.** It won't. `ProtoIntent` is direction, not a
  decision (Contract #4). If you need a choice, your host makes it.
- **Treating dormancy as failure.** `activated=False` on a confident step is
  the engine working correctly.
- **Feeding post-hoc state instead of the live contest.** LAE wants the
  *competing hypotheses at the moment of uncertainty*, not the winner after
  you've already resolved it.
- **Reaching past the facade.** `from lae import LAE` is the stable surface;
  the memory/identity submodules are internal and may change.

---

See [`../README.md`](../README.md) for the conceptual overview and
[`../CONTRACTS.md`](../CONTRACTS.md) for the non-negotiable invariants.
