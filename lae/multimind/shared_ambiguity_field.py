"""
lae.multimind.shared_ambiguity_field — Shared ambiguity fields (Phase 4).

Merges AmbiguityFields from multiple agents into one shared field.
Each agent perceives the same transition differently — different
regions, different conflict densities, different gradients. The merge
preserves provenance and never averages away disagreement:

- Regions present in multiple agents' fields are merged: coherence is
  averaged, but conflict_density takes the MAX (one agent seeing
  conflict means the conflict exists), and semantic_tags are unioned
  with agent provenance tags.
- Regions seen by only one agent become "minority regions" — kept,
  tagged with their single source. A minority report is still a report.
- Cross-agent disagreement creates new conflict edges: if agent A's
  gradient leans region X and agent B's leans region Y, X and Y gain a
  conflict_topology edge tagged cross_agent.
- Voids are intersected (a true void is unmapped by everyone) BUT
  agent-specific voids become coherence asymmetries: one agent's void
  that another agent maps is itself information.

Contract #2 holds at the collective level: shared ambiguity is mapped,
not collapsed. No agent's view is discarded.
"""

from __future__ import annotations

from ..types import AmbiguityField, Region


class SharedAmbiguityField:
    @staticmethod
    def merge(fields: dict[str, AmbiguityField]) -> AmbiguityField:
        """Merge per-agent fields into one shared field.

        Args:
            fields: {agent_id: AmbiguityField}
        """
        if not fields:
            return AmbiguityField(regions=[])
        if len(fields) == 1:
            return next(iter(fields.values()))

        # ------------------------------------------------------------------
        # Collect regions by ID across agents.
        region_sources: dict[str, list[tuple[str, Region]]] = {}
        for agent_id, f in fields.items():
            for r in f.regions:
                region_sources.setdefault(r.id, []).append((agent_id, r))

        merged_regions: list[Region] = []
        for rid, sources in region_sources.items():
            agents = [a for a, _ in sources]
            regions = [r for _, r in sources]
            coherence = round(sum(r.coherence_score for r in regions) / len(regions), 4)
            conflict = round(max(r.conflict_density for r in regions), 4)
            tags: list[str] = []
            for r in regions:
                for t in r.semantic_tags:
                    if t not in tags:
                        tags.append(t)
            if len(agents) < len(fields):
                tags.append("minority_region")
            for a in agents:
                tag = f"seen_by::{a}"
                if tag not in tags:
                    tags.append(tag)
            neighbors: list[str] = []
            for r in regions:
                for n in r.neighbors:
                    if n not in neighbors:
                        neighbors.append(n)
            merged_regions.append(
                Region(
                    id=rid,
                    conflict_density=conflict,
                    coherence_score=coherence,
                    semantic_tags=tags,
                    neighbors=neighbors,
                )
            )

        # ------------------------------------------------------------------
        # Merge gradients: mean per region, tracking per-agent leans.
        all_gradient_keys = set()
        for f in fields.values():
            all_gradient_keys.update(f.gradients.keys())
        merged_gradients: dict[str, float] = {}
        for key in all_gradient_keys:
            vals = [f.gradients.get(key, 0.0) for f in fields.values()]
            merged_gradients[key] = round(sum(vals) / len(vals), 4)

        # ------------------------------------------------------------------
        # Cross-agent disagreement -> conflict edges.
        merged_topology: dict[str, list[str]] = {}
        for f in fields.values():
            for rid, rivals in f.conflict_topology.items():
                for rival in rivals:
                    merged_topology.setdefault(rid, [])
                    if rival not in merged_topology[rid]:
                        merged_topology[rid].append(rival)

        agent_leans: dict[str, str] = {}
        for agent_id, f in fields.items():
            if f.gradients:
                agent_leans[agent_id] = max(f.gradients, key=f.gradients.get)
        leans = list(set(agent_leans.values()))
        for i, a in enumerate(leans):
            for b in leans[i + 1 :]:
                merged_topology.setdefault(a, [])
                if b not in merged_topology[a]:
                    merged_topology[a].append(b)
                merged_topology.setdefault(b, [])
                if a not in merged_topology[b]:
                    merged_topology[b].append(a)

        # ------------------------------------------------------------------
        # Voids: intersection = true voids. Asymmetric voids -> tags.
        void_sets = [set(f.voids) for f in fields.values()]
        true_voids = sorted(set.intersection(*void_sets)) if void_sets else []
        asymmetric = (set.union(*void_sets) - set(true_voids)) if void_sets else set()
        for r in merged_regions:
            if r.id in asymmetric and "coherence_asymmetry" not in r.semantic_tags:
                r.semantic_tags.append("coherence_asymmetry")

        # Islands: union (any agent's island is structurally interesting).
        islands: list[str] = []
        for f in fields.values():
            for i_ in f.coherence_islands:
                if i_ not in islands:
                    islands.append(i_)

        return AmbiguityField(
            regions=merged_regions,
            voids=true_voids,
            coherence_islands=islands,
            conflict_topology=merged_topology,
            gradients=merged_gradients,
        )
