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
- `multi_mind_demo.py` — Phase 4 collective transition merging: three agents with separate pipelines, a merged crossing when two or more destabilize together.
- `custom_hooks.py` — Phase 5 host integration: pre-transition vetoes, result annotation hooks, host-injected reconfiguration signals, and the event stream.

## Next Steps / Planned Examples

- `rfe_integration.py` — Example of wiring LAE as a sidecar to RFE-Core2
- `minimal_agent_loop.py` — Embedding LAE in a simple agent-style loop

Feel free to open an issue or PR if you'd like any of these prioritized.

---

**LAE** turns the messy, fragile moments between states into structured becoming.

The boundary is where the interesting things happen.
