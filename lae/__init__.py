"""Liminal Anchor Engine — a transition-layer subsystem for structured becoming.

Public API:

    from lae import LAE                      # stable external surface (Phase 5)
    from lae import LiminalAnchorEngine      # bare pipeline (no hooks/events)

    lae = LAE()
    outcome = lae.observe({"state_id": "calm", "hypotheses": {"a": 0.4, "b": 0.38}})

Canonical types (TYPES.md / schemas/) are importable from the top level.
"""

from .config import LAEConfig, load_config
from .integration.external_api import LAE, ObservationOutcome
from .pipeline import LiminalAnchorEngine, LiminalResult
from .types import (
    AmbiguityField,
    Anchor,
    IdentityGradient,
    LiminalMemoryEpisode,
    ProtoIntent,
    Region,
    TimeWindow,
    TransitionEvent,
)

__version__ = "0.5.0"

__all__ = [
    "LAE",
    "ObservationOutcome",
    "LiminalAnchorEngine",
    "LiminalResult",
    "LAEConfig",
    "load_config",
    "TransitionEvent",
    "TimeWindow",
    "Region",
    "AmbiguityField",
    "Anchor",
    "LiminalMemoryEpisode",
    "ProtoIntent",
    "IdentityGradient",
    "__version__",
]
