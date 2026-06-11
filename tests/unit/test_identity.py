"""Unit tests for the identity layer — Contract #6: identity is a
gradient field, never a fixed point."""

from __future__ import annotations

from lae.config import LAEConfig
from lae.identity.identity_field_model import (
    CRYSTALLIZATION_CEILING,
    IdentityFieldModel,
)
from lae.identity.invariance_tracker import (
    INVARIANCE_THRESHOLD,
    MIN_EPISODES,
    InvarianceTracker,
)
from lae.types import LiminalMemoryEpisode


def make_episode(protected: list[str], allowed: list[str] | None = None,
                 eid: str = "e") -> LiminalMemoryEpisode:
    return LiminalMemoryEpisode(
        episode_id=eid,
        source_state_id="src",
        target_state_ids=["t"],
        anchors_used=[],
        ambiguity_signature={
            "protected_features": protected,
            "allowed_mutations_seen": allowed or [],
        },
        identity_shift_delta={},
    )


# ---------------------------------------------------------------------------
# InvarianceTracker
# ---------------------------------------------------------------------------

def test_no_invariants_before_min_episodes():
    tracker = InvarianceTracker()
    for _ in range(MIN_EPISODES - 1):
        tracker.observe(make_episode(["core"]))
    assert tracker.invariant_candidates() == []


def test_consistently_protected_feature_becomes_invariant():
    tracker = InvarianceTracker()
    for _ in range(MIN_EPISODES):
        tracker.observe(make_episode(["core"]))
    assert "core" in tracker.invariant_candidates()


def test_allowed_mutation_disqualifies_invariance():
    """Regression: a feature an anchor explicitly allows to mutate can
    never graduate to invariant, even if heavily protected."""
    tracker = InvarianceTracker()
    tracker.observe(make_episode(["core"], allowed=["core"]))
    for _ in range(MIN_EPISODES):
        tracker.observe(make_episode(["core"]))
    assert "core" not in tracker.invariant_candidates()


def test_below_threshold_protection_not_invariant():
    tracker = InvarianceTracker()
    episodes = MIN_EPISODES * 2
    protected_count = int(episodes * INVARIANCE_THRESHOLD) - 1
    for i in range(episodes):
        tracker.observe(make_episode(["sometimes"] if i < protected_count else []))
    assert "sometimes" not in tracker.invariant_candidates()


def test_protection_rate():
    tracker = InvarianceTracker()
    tracker.observe(make_episode(["x"]))
    tracker.observe(make_episode([]))
    assert tracker.protection_rate("x") == 0.5
    assert tracker.protection_rate("unseen") == 0.0


# ---------------------------------------------------------------------------
# IdentityFieldModel
# ---------------------------------------------------------------------------

def test_trajectory_history_append_only():
    model = IdentityFieldModel(LAEConfig())
    model.apply_delta({"snapshot": {"step": 1}})
    model.apply_delta({"snapshot": {"step": 2}})
    assert [s["step"] for s in model.current.trajectory_history] == [1, 2]


def test_invariants_append_only():
    model = IdentityFieldModel(LAEConfig())
    model.apply_delta({"new_invariants": ["a"]})
    model.apply_delta({"new_invariants": ["a", "b"]})
    assert model.current.invariants == ["a", "b"]


def test_rigidity_clamped():
    model = IdentityFieldModel(LAEConfig())
    model.apply_delta({"rigidity_updates": {"x": 5.0, "y": -3.0}})
    # x clamps to <= 1.0 BEFORE the crystallization guard runs; the
    # guard may then soften it back below the ceiling since x is the
    # only... actually y exists at 0.0, so x stays clamped at 1.0.
    assert model.current.rigidity["y"] == 0.0
    assert model.current.rigidity["x"] <= 1.0


def test_crystallization_guard_keeps_one_plastic_feature():
    """Contract #6 / safety: identity cannot fully freeze."""
    model = IdentityFieldModel(LAEConfig())
    model.apply_delta({"rigidity_updates": {"x": 0.95, "y": 0.95}})
    non_invariant = model.current.rigidity
    assert any(v < CRYSTALLIZATION_CEILING for v in non_invariant.values())


def test_crystallization_guard_skips_invariants():
    model = IdentityFieldModel(LAEConfig())
    model.apply_delta({
        "new_invariants": ["core"],
        "rigidity_updates": {"core": 1.0, "edge": 0.95},
    })
    # "core" is invariant — allowed to stay rigid; "edge" must soften.
    assert model.current.rigidity["core"] == 1.0
    assert model.current.rigidity["edge"] < CRYSTALLIZATION_CEILING
