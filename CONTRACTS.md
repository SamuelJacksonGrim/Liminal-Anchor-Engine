# Liminal Anchor Engine (LAE)
## Internal Logic Contract

This document defines the invariant rules that every subsystem must obey.

If a module violates these, it is not part of LAE.

---

# 1. Transitions Are Primary

All computation is transition-centric.

- Detectors identify *leaving states*, not states.
- Memory stores *crossings*, not snapshots.
- Identity tracks *drift*, not attributes.

> States are temporary compressions of transition fields.

---

# 2. Ambiguity Must Be Structured

Ambiguity is a navigable space, not noise.

Every AmbiguityField must contain:

- regions (structured subspaces)
- gradients (directional uncertainty)
- voids (undefined model zones)
- coherence islands (local stability clusters)
- conflict topology (relationship graph of tensions)

If ambiguity is not structured → it is invalid.

---

# 3. Anchors Are Constraints, Not States

Anchors define continuity constraints during transformation.

Every Anchor must specify:

- protected_features
- allowed_mutations
- forbidden_mutations
- priority
- temporal_scope

> Anchors preserve identity continuity without freezing identity.

---

# 4. Intent Begins as Drift

ProtoIntent is not a decision.

It is a directional field emerging from ambiguity.

Every ProtoIntent must include:

- vector (directional pressure field)
- magnitude (strength of drift)
- stability_score (temporal coherence)
- origin_episode_ids (causal history)
- ambiguity_lineage (source uncertainty structure)

> Intent is pressure before choice.

---

# 5. Identity Is a Gradient Field

Identity is a dynamic manifold, not a fixed representation.

Every IdentityGradient must track:

- invariants (non-changing constraints)
- plasticity_zones (adaptable structure)
- rigidity_map (resistance to change)
- drift_vectors (direction of evolution)
- trajectory_history (temporal unfolding)

> Identity is motion across transition space.

---

# 6. Prime Directive

All modules must obey:

> Preserve continuity without preventing transformation.

This is the only global constraint.

---

# 7. System Validity Condition

A system state is valid only if:

- transitions are preserved as first-class objects
- ambiguity remains structured
- anchors preserve invariants without freezing dynamics
- proto-intents remain non-decisional
- identity remains gradient-based

Violation of any condition = invalid LAE state.
