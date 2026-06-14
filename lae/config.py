"""
lae.config — Runtime configuration.

Defaults mirror lae/CONFIG.yaml exactly. If PyYAML is installed and a
config path is supplied, values are loaded from file; otherwise the
in-code defaults apply. Zero hard dependencies by design (phone-first,
Codespaces-friendly).
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULTS: dict[str, Any] = {
    "version": 1.0,
    "activation": {
        "mode": "event_triggered",
        "triggers": [
            "confidence_collapse",
            "hypothesis_conflict",
            "frame_oscillation",
            "rapid_context_switch",
            "model_reconfiguration",
        ],
        "confidence_threshold": 0.4,
        "oscillation_window_ms": 1500,
    },
    "ambiguity_field": {
        "min_regions": 3,
        "include_voids": True,
        "include_coherence_islands": True,
        "include_conflict_graph": True,
    },
    "anchors": {
        "max_active_anchors": 12,
        "priority_bias": "identity_stability",
    },
    "memory": {
        "store_type": "episodic",
        "compression": "enabled",
        "index_by": "ambiguity_signature",
        # Cap the similarity scan to the most-recent N episodes so retrieval
        # stays O(1) per activation instead of O(memory size). 0 disables the
        # cap (scan everything). Stores smaller than the cap are unaffected.
        "retrieval_scan_limit": 512,
    },
    "intent": {
        "type": "proto_vector",
        "allow_non_deterministic": True,
    },
    "identity": {
        "representation": "gradient_field",
        "update_mode": "incremental",
    },
    "safety": {
        "prevent_identity_crystallization": True,
        "prevent_anchor_overconstraint": True,
        "preserve_transition_history": True,
    },
}


@dataclass
class LAEConfig:
    """Typed access to LAE configuration with CONFIG.yaml defaults."""

    # deepcopy: DEFAULTS holds nested dicts — a shallow copy would let one
    # engine's config mutations leak into every other instance.
    raw: dict[str, Any] = field(default_factory=lambda: copy.deepcopy(DEFAULTS))

    # -- activation --
    @property
    def confidence_threshold(self) -> float:
        return float(self.raw["activation"]["confidence_threshold"])

    @property
    def oscillation_window_ms(self) -> int:
        return int(self.raw["activation"]["oscillation_window_ms"])

    @property
    def triggers(self) -> list[str]:
        return list(self.raw["activation"]["triggers"])

    # -- ambiguity field --
    @property
    def min_regions(self) -> int:
        return int(self.raw["ambiguity_field"]["min_regions"])

    @property
    def include_voids(self) -> bool:
        return bool(self.raw["ambiguity_field"]["include_voids"])

    @property
    def include_coherence_islands(self) -> bool:
        return bool(self.raw["ambiguity_field"]["include_coherence_islands"])

    @property
    def include_conflict_graph(self) -> bool:
        return bool(self.raw["ambiguity_field"]["include_conflict_graph"])

    # -- anchors --
    @property
    def max_active_anchors(self) -> int:
        return int(self.raw["anchors"]["max_active_anchors"])

    @property
    def priority_bias(self) -> str:
        return str(self.raw["anchors"]["priority_bias"])

    # -- memory --
    @property
    def retrieval_scan_limit(self) -> int:
        return int(self.raw["memory"].get("retrieval_scan_limit", 0))

    # -- safety --
    @property
    def prevent_identity_crystallization(self) -> bool:
        return bool(self.raw["safety"]["prevent_identity_crystallization"])

    @property
    def prevent_anchor_overconstraint(self) -> bool:
        return bool(self.raw["safety"]["prevent_anchor_overconstraint"])

    @property
    def preserve_transition_history(self) -> bool:
        return bool(self.raw["safety"]["preserve_transition_history"])


def load_config(path: str | Path | None = None) -> LAEConfig:
    """Load config from YAML if available, else return defaults.

    Never raises on a missing yaml library or missing file — falls back
    to DEFAULTS so the engine always boots.
    """
    if path is None:
        return LAEConfig()
    try:
        import yaml  # type: ignore

        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        merged = copy.deepcopy(DEFAULTS)
        merged.update(data.get("lae", data))
        return LAEConfig(raw=merged)
    except Exception:
        return LAEConfig()
