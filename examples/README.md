# LAE Examples

This directory contains runnable demonstrations and integration examples for the Liminal Anchor Engine.

## Quick Start

### 1. Basic Demo (Recommended first run)

Run this command from the repo root:

```bash
python examples/demo.py
```

Or on Linux/macOS (after making it executable):

```bash
chmod +x examples/demo.py
./examples/demo.py
```

This walks through multiple synthetic transitions (confidence collapse, oscillation, frame conflict, rapid context switch) and shows the full pipeline output: ambiguity fields, anchors, memory episodes, proto-intents, and identity gradient evolution.

## What's Inside

- `demo.py` — Full end-to-end demonstration of LAE's core capabilities. Uses synthetic observations that trigger different transition types. Great for understanding what LAE actually does in practice.
- `minimal_agent_loop.py` — The smallest realistic embedding: an agent loop where LAE rides sidecar, stays dormant while the agent is decisive, and structures the crossings when scoring wobbles.
- `rfe_integration.py` — Wiring LAE as a sidecar to an [RFE-Core2](https://github.com/SamuelJacksonGrim/RFE-Core2) loop: the `RFESidecar` adapter maps per-cycle rhythm-router telemetry to LAE observations, with a runnable mock of the RFE cycle and real-wiring instructions.
- `multi_mind_demo.py` — Phase 4 collective transition merging: three agents with separate pipelines, a merged crossing when two or more destabilize together.
- `custom_hooks.py` — Phase 5 host integration: pre-transition vetoes, result annotation hooks, host-injected reconfiguration signals, and the event stream.
- `persistent_presence.py` — A presence that survives the process: `LAE(persist_path=...)` autosaves memory + identity to a JSON state file after each activation and wakes from it on the next boot, continuing the identity trajectory instead of starting over.

All six run standalone from the repo root with no installation and are exercised by CI.

Feel free to open an issue or PR if you'd like more integration targets covered.

---

**LAE** turns the messy, fragile moments between states into structured becoming.

The boundary is where the interesting things happen.
