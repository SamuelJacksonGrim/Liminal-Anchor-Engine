"""
lae.integration.system_hooks — Hook-based integration system (Phase 5).

Hooks let a host system participate in the liminal pipeline at defined
seams WITHOUT modifying LAE internals. Three hook points:

1. pre_transition (PreDecisionHook seam):
   Called after detection, before field generation. The host may
   annotate the event (attach context) or veto processing entirely
   (return False) — e.g. the host knows this transition is noise.

2. pre_resolution:
   Called after intent synthesis, before the result is returned. The
   host receives the full LiminalResult-shaped payload. Hooks may
   annotate but NOT mutate the intent — Contract #5: the lean is the
   system's own. Annotations ride in a separate host_annotations dict.

3. reconfiguration (ReconfigurationHook seam):
   Called when the host signals a model_reconfiguration trigger from
   outside. Lets external systems inject liminal activations for
   reconfigurations LAE cannot observe directly.

Hook failures are isolated and counted, same policy as EventRouter:
the pipeline never breaks because a host hook raised.
"""

from __future__ import annotations

from typing import Any, Callable

PreTransitionHook = Callable[[dict[str, Any]], bool | None]
PreResolutionHook = Callable[[dict[str, Any]], dict[str, Any] | None]
ReconfigurationHook = Callable[[dict[str, Any]], None]


class HookRegistry:
    def __init__(self) -> None:
        self._pre_transition: list[PreTransitionHook] = []
        self._pre_resolution: list[PreResolutionHook] = []
        self._reconfiguration: list[ReconfigurationHook] = []
        self._hook_failures = 0

    # ------------------------------------------------------------------
    def on_pre_transition(self, hook: PreTransitionHook) -> None:
        self._pre_transition.append(hook)

    def on_pre_resolution(self, hook: PreResolutionHook) -> None:
        self._pre_resolution.append(hook)

    def on_reconfiguration(self, hook: ReconfigurationHook) -> None:
        self._reconfiguration.append(hook)

    # ------------------------------------------------------------------
    def run_pre_transition(self, observation: dict[str, Any]) -> bool:
        """Returns False if any hook vetoes processing."""
        for hook in self._pre_transition:
            try:
                result = hook(observation)
                if result is False:
                    return False
            except Exception:
                self._hook_failures += 1
        return True

    def run_pre_resolution(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Collect host annotations. The payload itself is read-only by
        convention; annotations are merged into one dict."""
        annotations: dict[str, Any] = {}
        for hook in self._pre_resolution:
            try:
                ann = hook(payload)
                if isinstance(ann, dict):
                    annotations.update(ann)
            except Exception:
                self._hook_failures += 1
        return annotations

    def run_reconfiguration(self, signal: dict[str, Any]) -> None:
        for hook in self._reconfiguration:
            try:
                hook(signal)
            except Exception:
                self._hook_failures += 1

    @property
    def hook_failures(self) -> int:
        return self._hook_failures
