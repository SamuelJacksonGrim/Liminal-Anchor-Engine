"""Shared fixtures for the LAE pytest suite."""

from __future__ import annotations

import pytest

from lae.config import LAEConfig
from lae.fields.ambiguity_field import AmbiguityFieldGenerator
from lae.types import TimeWindow, TransitionEvent


@pytest.fixture
def config() -> LAEConfig:
    return LAEConfig()


@pytest.fixture
def make_event():
    """Factory for synthetic TransitionEvents."""

    def _make(
        source: str = "state::origin",
        profile: dict[str, float] | None = None,
        conflict: float = 0.8,
        start: float = 0.0,
        end: float = 1.5,
    ) -> TransitionEvent:
        profile = profile or {"state::a": 0.35, "state::b": 0.33, "state::c": 0.30}
        return TransitionEvent(
            source_state_id=source,
            candidate_target_states=sorted(profile, key=profile.get, reverse=True),
            confidence_profile=profile,
            conflict_score=conflict,
            time_window=TimeWindow(start=start, end=end),
        )

    return _make


@pytest.fixture
def make_field(make_event, config):
    """Factory for AmbiguityFields generated from synthetic events."""

    generator = AmbiguityFieldGenerator(config)

    def _make(**event_kwargs):
        return generator.generate(make_event(**event_kwargs))

    return _make
