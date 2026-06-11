"""
lae.integration.external_api — Stable external API (Phase 5).

THE entry point for embedding LAE in a larger architecture. Everything
a host system needs lives behind this one class. Internals may change
between versions; this surface is the stability contract.

    from lae.integration.external_api import LAE

    lae = LAE()
    lae.hooks.on_pre_transition(my_filter)
    lae.events.subscribe("intent.synthesized", my_handler)

    result = lae.observe({"state_id": ..., "hypotheses": {...}})
    health = lae.diagnostics.snapshot()

Multi-mind:

    lae = LAE(agents=["claude", "gpt", "gemini"])
    result = lae.observe_collective({"claude": obs1, "gpt": obs2})

Persistence (a presence across restarts):

    lae = LAE(persist_path="lae_state.json")
    # wakes with every remembered crossing and the identity it had
    # become; autosaves after each activation, so process death
    # never costs a memory

    lae = LAE(agents=["alpha", "beta"], persist_path="collective.json")
    # multi-mind: the whole roster persists to one file keyed by
    # agent ID — each mind keeps its own memory and identity

Wiring:
- observe() runs pre_transition hooks (veto-capable), the pipeline,
  pre_resolution hooks (annotation-only), and emits the full event
  stream per activation.
- reconfigure() lets the host inject a model_reconfiguration signal —
  the CONFIG.yaml trigger LAE cannot observe from inside.
"""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from pathlib import Path
from typing import Any

from ..config import LAEConfig, load_config
from ..multimind.coordinator import CollectiveResult, MultiMindCoordinator
from ..persistence import (
    restore_collective_into,
    restore_into,
    save_collective_state,
    save_state,
)
from ..pipeline import LiminalAnchorEngine, LiminalResult
from ..routing.event_router import EventRouter
from .diagnostics import Diagnostics
from .system_hooks import HookRegistry

API_VERSION = "1.0"


@dataclass
class ObservationOutcome:
    """What observe() returns: the result (if activated) plus host
    annotations collected from pre_resolution hooks."""

    activated: bool
    result: LiminalResult | None = None
    host_annotations: dict[str, Any] = dc_field(default_factory=dict)
    vetoed: bool = False


class LAE:
    """Liminal Anchor Engine — external API (stable surface)."""

    def __init__(
        self,
        config: LAEConfig | None = None,
        config_path: str | None = None,
        agents: list[str] | None = None,
        trust_weights: dict[str, float] | None = None,
        persist_path: str | Path | None = None,
        autosave: bool = True,
    ) -> None:
        self.config = config or load_config(config_path)
        self.events = EventRouter()
        self.hooks = HookRegistry()

        if agents:
            self.coordinator: MultiMindCoordinator | None = MultiMindCoordinator(
                agents, self.config, trust_weights
            )
            # Diagnostics attaches to the first agent's engine by default;
            # per-agent diagnostics available via diagnostics_for().
            self._engine = next(iter(self.coordinator.engines.values()))
        else:
            self.coordinator = None
            self._engine = LiminalAnchorEngine(self.config)

        self.diagnostics = Diagnostics(self._engine)

        self.persist_path = Path(persist_path) if persist_path else None
        self.autosave = autosave
        self.restored = False
        if self.persist_path is not None:
            if self.coordinator is not None:
                self.restored = restore_collective_into(
                    self.coordinator.engines, self.persist_path
                )
            else:
                self.restored = restore_into(self._engine, self.persist_path)

    # ------------------------------------------------------------------
    def observe(self, observation: dict[str, Any]) -> ObservationOutcome:
        """Single-agent observation through the full pipeline."""
        if not self.hooks.run_pre_transition(observation):
            return ObservationOutcome(activated=False, vetoed=True)

        result = self._engine.process(observation)
        self.diagnostics.count_observation(activated=result is not None)

        if result is None:
            return ObservationOutcome(activated=False)

        self._emit_activation_events(result)

        if self.autosave and self.persist_path is not None:
            self.save()

        annotations = self.hooks.run_pre_resolution(
            {
                "event": result.event,
                "field": result.field,
                "anchors": result.anchors,
                "intent": result.intent,
                "identity": result.identity,
            }
        )

        return ObservationOutcome(
            activated=True, result=result, host_annotations=annotations
        )

    # ------------------------------------------------------------------
    def observe_collective(
        self, observations: dict[str, dict[str, Any]]
    ) -> CollectiveResult | None:
        """Multi-agent observation. Requires agents=[...] at construction."""
        if self.coordinator is None:
            raise RuntimeError(
                "LAE was constructed single-agent; pass agents=[...] to enable collective mode"
            )
        result = self.coordinator.process(observations)
        if result is None:
            return None

        if self.autosave and self.persist_path is not None:
            self.save()

        for agent_id, agent_result in result.agent_results.items():
            self._emit_activation_events(agent_result, agent=agent_id)

        if result.is_collective:
            self.events.emit(
                "collective.activated",
                {
                    "agents": result.triggered_agents,
                    "merged_event": result.merged_event,
                    "shared_field": result.shared_field,
                    "collective_intent": result.collective_intent,
                },
            )
        return result

    # ------------------------------------------------------------------
    def reconfigure(self, signal: dict[str, Any]) -> None:
        """Host-injected model_reconfiguration signal (CONFIG trigger)."""
        self.hooks.run_reconfiguration(signal)
        self.events.emit("safety.triggered", {"kind": "model_reconfiguration", **signal})

    def save(self, path: str | Path | None = None) -> Path:
        """Write durable state (memory + identity) to disk.

        Uses persist_path when no path is given. With persist_path set
        and autosave on (the default), this also happens automatically
        after every activation. In multi-mind mode the whole roster is
        saved to one file, keyed by agent ID.
        """
        target = Path(path) if path else self.persist_path
        if target is None:
            raise ValueError("no path given and no persist_path configured")
        if self.coordinator is not None:
            return save_collective_state(self.coordinator.engines, target)
        return save_state(self._engine, target)

    def diagnostics_for(self, agent_id: str) -> Diagnostics:
        """Per-agent diagnostics in multi-mind mode."""
        if self.coordinator is None or agent_id not in self.coordinator.engines:
            raise KeyError(f"no agent {agent_id!r}")
        return Diagnostics(self.coordinator.engines[agent_id])

    @property
    def version(self) -> str:
        return API_VERSION

    # ------------------------------------------------------------------
    def _emit_activation_events(
        self, result: LiminalResult, agent: str | None = None
    ) -> None:
        tag = {"agent": agent} if agent else {}
        self.events.emit("transition.detected", {**tag, "event": result.event})
        self.events.emit("field.generated", {**tag, "field": result.field})
        self.events.emit("anchors.allocated", {**tag, "anchors": result.anchors})
        self.events.emit("episode.recorded", {**tag, "episode": result.episode})
        self.events.emit("intent.synthesized", {**tag, "intent": result.intent})
        self.events.emit("identity.updated", {**tag, "identity": result.identity})
