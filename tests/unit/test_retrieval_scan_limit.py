"""Retrieval scan-limit: similarity search must stay bounded as memory grows
so per-activation cost does not climb with episode count."""

from __future__ import annotations

from lae.config import LAEConfig
from lae.memory.ambiguity_signature_index import AmbiguitySignatureIndex
from lae.memory.liminal_memory_buffer import LiminalMemoryBuffer


def _sig(region_count):
    return {
        "region_count": region_count,
        "void_count": 0,
        "island_count": 0,
        "conflict_edge_count": 0,
        "mean_conflict_density": 0.0,
    }


def test_scan_limit_bounds_entries_considered():
    """An old, distinctive episode beyond the scan window is not returned;
    only the most-recent `scan_limit` entries are scored."""
    idx = AmbiguitySignatureIndex(scan_limit=3)
    idx.insert("episode::old", _sig(99))  # distinctive, then buried
    for i in range(5):
        idx.insert(f"episode::new{i}", _sig(1))
    returned = {eid for eid, _ in idx.top_k(_sig(99), k=10)}
    assert "episode::old" not in returned
    assert len(returned) == 3  # window size


def test_scan_limit_zero_is_unbounded():
    idx = AmbiguitySignatureIndex(scan_limit=0)
    idx.insert("episode::old", _sig(99))
    for i in range(5):
        idx.insert(f"episode::new{i}", _sig(1))
    returned = {eid for eid, _ in idx.top_k(_sig(99), k=10)}
    assert "episode::old" in returned


def test_small_store_unaffected_by_cap():
    """Stores smaller than the cap behave exactly as an unbounded scan."""
    capped = AmbiguitySignatureIndex(scan_limit=512)
    full = AmbiguitySignatureIndex(scan_limit=0)
    for i in range(10):
        capped.insert(f"e{i}", _sig(i))
        full.insert(f"e{i}", _sig(i))
    assert capped.top_k(_sig(3), k=5) == full.top_k(_sig(3), k=5)


def test_config_default_and_wiring():
    cfg = LAEConfig()
    assert cfg.retrieval_scan_limit == 512
    buffer = LiminalMemoryBuffer(cfg)
    assert buffer._index.scan_limit == 512


def test_config_override_flows_to_index():
    cfg = LAEConfig()
    cfg.raw["memory"]["retrieval_scan_limit"] = 0
    buffer = LiminalMemoryBuffer(cfg)
    assert buffer._index.scan_limit == 0
