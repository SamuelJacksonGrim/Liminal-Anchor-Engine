# LAE Examples

This directory contains runnable demonstrations and integration examples for the **Liminal Anchor Engine**.

## Quick Start

### Basic Demo (Recommended)

From the root of the repository, run:

```bash
python examples/demo.py
```

Linux / macOS users can also make it directly executable:

```bash
chmod +x examples/demo.py
./examples/demo.py
```

The demo runs a series of synthetic transitions and prints the full LAE pipeline: TransitionEvent, AmbiguityField, Anchors, LiminalMemoryEpisode, ProtoIntent, and IdentityGradient.

## What's Inside

- **`demo.py`** — Complete end-to-end demonstration of the core LAE capabilities.

## Planned / Future Examples

- `rfe_integration.py` — Wiring LAE as a sidecar to RFE-Core2
- `multi_mind_demo.py` — Phase 4 collective/multi-agent transitions
- `custom_hooks.py` — Using pre-transition vetoes and annotation hooks

---

**LAE** turns turbulent transitions into structured becoming.

The boundary is where the interesting things happen.
