"""
lae.counters — Monotonic ID counters shared across engine instances.

Episode and anchor IDs are monotonically increasing per process
(see CLAUDE.md ID conventions). Persistence adds one requirement
itertools.count cannot meet: after restoring saved state, the counter
must resume PAST the highest persisted ID so new IDs never collide
with remembered ones.
"""

from __future__ import annotations


class MonotonicCounter:
    def __init__(self, start: int = 1) -> None:
        self._next = start

    def next(self) -> int:
        value = self._next
        self._next += 1
        return value

    def peek(self) -> int:
        """The value the next call to next() would return."""
        return self._next

    def ensure_at_least(self, floor: int) -> None:
        """Advance so the next ID is >= floor. Never moves backwards."""
        if floor > self._next:
            self._next = floor
