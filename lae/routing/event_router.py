"""
lae.routing.event_router — Event streaming architecture (Phase 5).

Layer 7. The router turns pipeline outputs into a typed event stream
that external systems subscribe to. Synchronous, in-process, ordered —
no external message broker required (phone-first, zero deps).

Event types emitted:
    transition.detected      — TransitionEvent produced
    field.generated          — AmbiguityField built
    anchors.allocated        — anchor set ready
    episode.recorded         — memory write committed
    intent.synthesized       — proto-intent ready
    identity.updated         — identity gradient moved
    collective.activated     — multi-mind collective layer fired
    safety.triggered         — any safety guard intervened

Subscribers register callbacks per event type or "*" for all.
Subscriber exceptions are isolated — one failing subscriber never
breaks the stream or other subscribers. Failures are counted and
visible via diagnostics.

Events are dicts with a stable envelope:
    {"type": str, "seq": int, "timestamp": float, "payload": Any}
"""

from __future__ import annotations

import itertools
import time
from collections import defaultdict
from typing import Any, Callable

EventCallback = Callable[[dict[str, Any]], None]

EVENT_TYPES = (
    "transition.detected",
    "field.generated",
    "anchors.allocated",
    "episode.recorded",
    "intent.synthesized",
    "identity.updated",
    "collective.activated",
    "safety.triggered",
)


class EventRouter:
    def __init__(self, history_limit: int = 200) -> None:
        self._subscribers: dict[str, list[EventCallback]] = defaultdict(list)
        self._seq = itertools.count(1)
        self._history: list[dict[str, Any]] = []
        self._history_limit = history_limit
        self._delivery_failures = 0

    # ------------------------------------------------------------------
    def subscribe(self, event_type: str, callback: EventCallback) -> None:
        """Register a callback for an event type, or '*' for all."""
        self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback: EventCallback) -> None:
        if callback in self._subscribers.get(event_type, []):
            self._subscribers[event_type].remove(callback)

    # ------------------------------------------------------------------
    def emit(self, event_type: str, payload: Any) -> dict[str, Any]:
        """Emit an event to all matching subscribers. Returns the envelope."""
        event = {
            "type": event_type,
            "seq": next(self._seq),
            "timestamp": time.time(),
            "payload": payload,
        }
        self._history.append(event)
        if len(self._history) > self._history_limit:
            self._history = self._history[-self._history_limit:]

        for cb in list(self._subscribers.get(event_type, [])) + list(
            self._subscribers.get("*", [])
        ):
            try:
                cb(event)
            except Exception:
                self._delivery_failures += 1

        return event

    # ------------------------------------------------------------------
    def recent(self, n: int = 20, event_type: str | None = None) -> list[dict[str, Any]]:
        events = self._history
        if event_type:
            events = [e for e in events if e["type"] == event_type]
        return events[-n:]

    @property
    def delivery_failures(self) -> int:
        return self._delivery_failures
