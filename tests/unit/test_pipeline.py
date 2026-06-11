"""End-to-end pipeline and external API tests."""

from __future__ import annotations

from lae import LAE, LiminalAnchorEngine
from lae.config import LAEConfig


def unstable_obs(ts: float = 0.0) -> dict:
    return {
        "state_id": "origin",
        "hypotheses": {"a": 0.31, "b": 0.30, "c": 0.28},
        "timestamp": ts,
    }


def stable_obs(ts: float = 0.0) -> dict:
    return {
        "state_id": "origin",
        "hypotheses": {"winner": 0.92, "noise": 0.04},
        "timestamp": ts,
    }


# ---------------------------------------------------------------------------
# Bare pipeline
# ---------------------------------------------------------------------------

def test_stable_observation_returns_none():
    engine = LiminalAnchorEngine(LAEConfig())
    assert engine.process(stable_obs()) is None


def test_unstable_observation_activates_full_pipeline():
    engine = LiminalAnchorEngine(LAEConfig())
    result = engine.process(unstable_obs())
    assert result is not None
    assert result.event.source_state_id == "origin"
    assert result.field.regions
    assert result.anchors
    assert result.episode.episode_id
    assert result.intent.magnitude >= 0.0
    assert result.identity.trajectory_history


def test_episode_carries_identity_delta():
    engine = LiminalAnchorEngine(LAEConfig())
    result = engine.process(unstable_obs())
    assert result.episode.identity_shift_delta, "delta must not be empty"


def test_memory_accumulates_across_activations():
    engine = LiminalAnchorEngine(LAEConfig())
    first = engine.process(unstable_obs(0.0))
    second = engine.process(unstable_obs(10.0))
    assert first.episode.episode_id != second.episode.episode_id
    # The second crossing should see the first as a precedent.
    assert first.episode.episode_id in second.intent.origin_episode_ids


def test_engines_are_isolated():
    """Two engines must not share memory, identity, or config state."""
    e1 = LiminalAnchorEngine(LAEConfig())
    e2 = LiminalAnchorEngine(LAEConfig())
    e1.process(unstable_obs())
    assert len(e1.memory) == 1
    assert len(e2.memory) == 0
    assert e2.identity_mapper.field_model.current.trajectory_history == []


# ---------------------------------------------------------------------------
# External API (LAE)
# ---------------------------------------------------------------------------

def test_lae_observe_outcome_shape():
    api = LAE()
    out = api.observe(unstable_obs())
    assert out.activated is True
    assert out.result is not None
    assert out.vetoed is False


def test_lae_dormant_on_stable():
    api = LAE()
    out = api.observe(stable_obs())
    assert out.activated is False
    assert out.result is None


def test_lae_pre_transition_veto():
    api = LAE()
    api.hooks.on_pre_transition(lambda obs: False)
    out = api.observe(unstable_obs())
    assert out.vetoed is True
    assert out.activated is False


def test_lae_event_stream_order():
    api = LAE()
    seen: list[str] = []
    for topic in [
        "transition.detected", "field.generated", "anchors.allocated",
        "episode.recorded", "intent.synthesized", "identity.updated",
    ]:
        api.events.subscribe(topic, lambda payload, t=topic: seen.append(t))
    api.observe(unstable_obs())
    assert seen == [
        "transition.detected", "field.generated", "anchors.allocated",
        "episode.recorded", "intent.synthesized", "identity.updated",
    ]


def test_lae_collective_requires_agents():
    import pytest

    api = LAE()
    with pytest.raises(RuntimeError):
        api.observe_collective({"a": unstable_obs()})


def test_lae_multimind_collective_activation():
    api = LAE(agents=["alpha", "beta"])
    out = api.observe_collective({
        "alpha": unstable_obs(),
        "beta": {
            "state_id": "origin",
            "hypotheses": {"a": 0.33, "b": 0.32, "c": 0.25},
            "timestamp": 0.0,
        },
    })
    assert out is not None
    assert set(out.triggered_agents) == {"alpha", "beta"}
