"""Unit tests for TransitionDetector — each trigger rule in isolation."""

from __future__ import annotations

from lae.config import LAEConfig
from lae.detectors.transition_detector import TransitionDetector


def make_detector() -> TransitionDetector:
    return TransitionDetector(LAEConfig())


def test_no_hypotheses_returns_none():
    det = make_detector()
    assert det.observe({"state_id": "s", "hypotheses": {}, "timestamp": 0.0}) is None


def test_stable_state_returns_none():
    det = make_detector()
    obs = {
        "state_id": "s",
        "hypotheses": {"winner": 0.92, "loser": 0.05},
        "timestamp": 0.0,
    }
    assert det.observe(obs) is None


def test_confidence_collapse_fires():
    det = make_detector()
    obs = {
        "state_id": "s",
        # Top confidence below the 0.4 threshold, gap above conflict band.
        "hypotheses": {"a": 0.35, "b": 0.10},
        "timestamp": 0.0,
    }
    event = det.observe(obs)
    assert event is not None
    assert event.source_state_id == "s"
    assert event.candidate_target_states[0] == "a"


def test_hypothesis_conflict_fires():
    det = make_detector()
    obs = {
        "state_id": "s",
        # Both above threshold but within the 0.15 conflict band.
        "hypotheses": {"a": 0.60, "b": 0.55},
        "timestamp": 0.0,
    }
    event = det.observe(obs)
    assert event is not None
    assert event.conflict_score > 0.0


def test_frame_oscillation_fires_on_flip_flop():
    det = make_detector()
    # Alternate the top hypothesis well inside the oscillation window.
    # Keep individual observations stable (high top confidence, wide gap)
    # so only oscillation can be the trigger.
    seq = [
        ({"a": 0.9, "b": 0.05}, 0.0),
        ({"a": 0.05, "b": 0.9}, 0.1),
        ({"a": 0.9, "b": 0.05}, 0.2),
    ]
    events = [
        det.observe({"state_id": "s", "hypotheses": h, "timestamp": t})
        for h, t in seq
    ]
    assert events[0] is None
    assert events[1] is None
    assert events[2] is not None


def test_oscillation_outside_window_does_not_fire():
    det = make_detector()
    window_s = det.config.oscillation_window_ms / 1000.0
    seq = [
        ({"a": 0.9, "b": 0.05}, 0.0),
        ({"a": 0.05, "b": 0.9}, window_s * 2),
        ({"a": 0.9, "b": 0.05}, window_s * 4),
    ]
    for h, t in seq:
        assert det.observe({"state_id": "s", "hypotheses": h, "timestamp": t}) is None


def test_conflict_score_bounds():
    uniform = {"a": 0.25, "b": 0.25, "c": 0.25, "d": 0.25}
    assert TransitionDetector._conflict_score(uniform) == 1.0
    dominant = {"a": 1.0, "b": 0.0}
    assert TransitionDetector._conflict_score(dominant) == 0.0
    single = {"a": 0.4}
    assert TransitionDetector._conflict_score(single) == 0.0


def test_candidates_sorted_by_confidence():
    det = make_detector()
    event = det.observe(
        {"state_id": "s", "hypotheses": {"low": 0.1, "high": 0.3, "mid": 0.2}}
    )
    assert event is not None
    assert event.candidate_target_states == ["high", "mid", "low"]
