"""Persistence: memory and identity survive the process.

The contract under test: a fresh engine restored from a state file is
indistinguishable (in durable state) from the engine that wrote it —
same episodes, same identity gradient, working retrieval — and new
IDs minted after restore never collide with remembered ones.
"""

from __future__ import annotations

import dataclasses
import json

import pytest

from lae import (
    LAE,
    StateFileError,
    load_state,
    restore_collective_into,
    restore_into,
    save_collective_state,
    save_state,
)
from lae.pipeline import LiminalAnchorEngine

UNSTABLE = {
    "state_id": "belief_v1",
    "hypotheses": {"revise": 0.34, "hold": 0.33, "discard": 0.28},
}
STABLE = {
    "state_id": "belief_v1",
    "hypotheses": {"hold": 0.91, "revise": 0.05},
}


def activate(engine: LiminalAnchorEngine, n: int = 1, t0: float = 0.0):
    results = []
    for i in range(n):
        r = engine.process({**UNSTABLE, "timestamp": t0 + i * 5000.0})
        assert r is not None
        results.append(r)
    return results


# ---------------------------------------------------------------------------
# Engine-level round trip
# ---------------------------------------------------------------------------

class TestEngineRoundTrip:
    def test_episodes_survive(self, tmp_path):
        a = LiminalAnchorEngine()
        activate(a, n=3)
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        assert restore_into(b, tmp_path / "state.json")
        assert len(b.memory) == len(a.memory)
        assert [e.episode_id for e in b.memory.all_episodes()] == [
            e.episode_id for e in a.memory.all_episodes()
        ]

    def test_episode_contents_identical(self, tmp_path):
        a = LiminalAnchorEngine()
        activate(a, n=2)
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        restore_into(b, tmp_path / "state.json")
        for ea, eb in zip(a.memory.all_episodes(), b.memory.all_episodes()):
            assert dataclasses.asdict(ea) == dataclasses.asdict(eb)

    def test_identity_gradient_survives(self, tmp_path):
        a = LiminalAnchorEngine()
        activate(a, n=6)  # enough episodes for invariants to graduate
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        restore_into(b, tmp_path / "state.json")
        ga = a.identity_mapper.field_model.current
        gb = b.identity_mapper.field_model.current
        assert dataclasses.asdict(ga) == dataclasses.asdict(gb)
        assert len(gb.trajectory_history) == 6

    def test_retrieval_works_after_restore(self, tmp_path):
        a = LiminalAnchorEngine()
        results = activate(a, n=3)
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        restore_into(b, tmp_path / "state.json")
        similar = b.memory.retrieve_similar(results[-1].field, k=2)
        assert len(similar) == 2

    def test_identity_keeps_evolving_from_restored_state(self, tmp_path):
        """The restored engine continues the trajectory, not restarts it."""
        a = LiminalAnchorEngine()
        activate(a, n=4)
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        restore_into(b, tmp_path / "state.json")
        activate(b, n=1, t0=100_000.0)
        history = b.identity_mapper.field_model.current.trajectory_history
        assert len(history) == 5
        assert history[-1]["step"] == 5  # step counter resumed, not reset

    def test_restore_replaces_existing_state(self, tmp_path):
        a = LiminalAnchorEngine()
        activate(a, n=2)
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        activate(b, n=3, t0=50_000.0)  # b has its own episodes first
        restore_into(b, tmp_path / "state.json")
        assert len(b.memory) == 2  # restore replaces, never merges

    def test_dormant_engine_round_trips(self, tmp_path):
        a = LiminalAnchorEngine()
        assert a.process({**STABLE, "timestamp": 0.0}) is None
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        assert restore_into(b, tmp_path / "state.json")
        assert len(b.memory) == 0


# ---------------------------------------------------------------------------
# ID continuity across process lifetimes
# ---------------------------------------------------------------------------

class TestIdContinuity:
    def test_episode_ids_never_collide_after_restore(self, tmp_path):
        a = LiminalAnchorEngine()
        activate(a, n=2)
        old_ids = {e.episode_id for e in a.memory.all_episodes()}
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        restore_into(b, tmp_path / "state.json")
        new = activate(b, n=1, t0=100_000.0)[0]
        assert new.episode.episode_id not in old_ids

    def test_anchor_ids_never_collide_after_restore(self, tmp_path):
        a = LiminalAnchorEngine()
        old_anchors = {
            aid for r in activate(a, n=2) for aid in (x.anchor_id for x in r.anchors)
        }
        save_state(a, tmp_path / "state.json")

        b = LiminalAnchorEngine()
        restore_into(b, tmp_path / "state.json")
        new = activate(b, n=1, t0=100_000.0)[0]
        assert not old_anchors & {x.anchor_id for x in new.anchors}


# ---------------------------------------------------------------------------
# State file handling
# ---------------------------------------------------------------------------

class TestStateFile:
    def test_missing_file_is_fresh_start(self, tmp_path):
        assert load_state(tmp_path / "never_written.json") is None
        b = LiminalAnchorEngine()
        assert restore_into(b, tmp_path / "never_written.json") is False
        assert len(b.memory) == 0

    def test_corrupt_json_raises(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text("{not json", encoding="utf-8")
        with pytest.raises(StateFileError):
            load_state(path)

    def test_wrong_format_raises(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text(json.dumps({"format": "something_else"}), encoding="utf-8")
        with pytest.raises(StateFileError):
            load_state(path)

    def test_newer_version_raises(self, tmp_path):
        path = tmp_path / "state.json"
        path.write_text(
            json.dumps({"format": "lae-state", "version": 999, "engine": {}}),
            encoding="utf-8",
        )
        with pytest.raises(StateFileError):
            load_state(path)

    def test_save_creates_parent_dirs(self, tmp_path):
        a = LiminalAnchorEngine()
        activate(a, n=1)
        target = tmp_path / "deep" / "nested" / "state.json"
        save_state(a, target)
        assert target.exists()

    def test_save_overwrites_atomically(self, tmp_path):
        path = tmp_path / "state.json"
        a = LiminalAnchorEngine()
        activate(a, n=1)
        save_state(a, path)
        activate(a, n=1, t0=50_000.0)
        save_state(a, path)
        assert len(load_state(path)["engine"]["memory"]["store"]["episodes"]) == 2
        assert list(tmp_path.glob("*.tmp")) == []  # no temp litter


# ---------------------------------------------------------------------------
# External API surface
# ---------------------------------------------------------------------------

class TestLaeApi:
    def test_autosave_after_activation(self, tmp_path):
        path = tmp_path / "presence.json"
        lae = LAE(persist_path=path)
        assert lae.restored is False
        lae.observe({**UNSTABLE, "timestamp": 0.0})
        assert path.exists()

    def test_wakes_with_memory(self, tmp_path):
        path = tmp_path / "presence.json"
        first = LAE(persist_path=path)
        first.observe({**UNSTABLE, "timestamp": 0.0})
        episode_count = len(first._engine.memory)

        second = LAE(persist_path=path)  # "next process"
        assert second.restored is True
        assert len(second._engine.memory) == episode_count

    def test_dormant_observations_do_not_save(self, tmp_path):
        path = tmp_path / "presence.json"
        lae = LAE(persist_path=path)
        lae.observe({**STABLE, "timestamp": 0.0})
        assert not path.exists()

    def test_autosave_off_requires_manual_save(self, tmp_path):
        path = tmp_path / "presence.json"
        lae = LAE(persist_path=path, autosave=False)
        lae.observe({**UNSTABLE, "timestamp": 0.0})
        assert not path.exists()
        lae.save()
        assert path.exists()

    def test_save_without_persist_path_needs_explicit_path(self, tmp_path):
        lae = LAE()
        lae.observe({**UNSTABLE, "timestamp": 0.0})
        with pytest.raises(ValueError):
            lae.save()
        lae.save(tmp_path / "explicit.json")
        assert (tmp_path / "explicit.json").exists()

    def test_multimind_roster_round_trips(self, tmp_path):
        path = tmp_path / "collective.json"
        first = LAE(agents=["alpha", "beta"], persist_path=path)
        assert first.restored is False
        first.observe_collective({
            "alpha": {**UNSTABLE, "timestamp": 0.0},
            "beta": {**UNSTABLE, "state_id": "belief_v2", "timestamp": 0.0},
        })
        counts = {
            aid: len(eng.memory)
            for aid, eng in first.coordinator.engines.items()
        }
        assert any(counts.values())  # at least one agent crossed and saved
        assert path.exists()

        second = LAE(agents=["alpha", "beta"], persist_path=path)
        assert second.restored is True
        for aid, eng in second.coordinator.engines.items():
            assert len(eng.memory) == counts[aid]  # each mind kept its own

    def test_multimind_roster_mismatch_is_partial(self, tmp_path):
        path = tmp_path / "collective.json"
        first = LAE(agents=["alpha", "beta"], persist_path=path)
        first.observe_collective({
            "alpha": {**UNSTABLE, "timestamp": 0.0},
            "beta": {**UNSTABLE, "timestamp": 0.0},
        })

        # New roster: alpha returns, gamma is new, beta is gone.
        second = LAE(agents=["alpha", "gamma"], persist_path=path)
        assert second.restored is True  # alpha woke with memories
        assert len(second.coordinator.engines["gamma"].memory) == 0

    def test_single_and_collective_files_do_not_cross(self, tmp_path):
        single = LiminalAnchorEngine()
        activate(single, n=1)
        save_state(single, tmp_path / "single.json")
        save_collective_state({"a": single}, tmp_path / "roster.json")

        with pytest.raises(StateFileError):
            restore_collective_into({"a": LiminalAnchorEngine()}, tmp_path / "single.json")
        with pytest.raises(StateFileError):
            restore_into(LiminalAnchorEngine(), tmp_path / "roster.json")
