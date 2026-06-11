"""Config tests — defaults, instance isolation, YAML fallback behavior."""

from __future__ import annotations

from lae.config import DEFAULTS, LAEConfig, load_config


def test_defaults_load():
    cfg = LAEConfig()
    assert cfg.confidence_threshold == 0.4
    assert cfg.oscillation_window_ms == 1500
    assert cfg.min_regions == 3
    assert cfg.max_active_anchors == 12
    assert cfg.prevent_identity_crystallization is True
    assert cfg.prevent_anchor_overconstraint is True


def test_config_instances_are_isolated():
    """Regression: mutating one config's nested dicts must not leak into
    other instances or the module-level DEFAULTS."""
    a = LAEConfig()
    b = LAEConfig()
    a.raw["activation"]["confidence_threshold"] = 0.99
    assert b.confidence_threshold == 0.4
    assert DEFAULTS["activation"]["confidence_threshold"] == 0.4


def test_load_config_none_path_returns_defaults():
    cfg = load_config(None)
    assert cfg.confidence_threshold == 0.4


def test_load_config_missing_file_falls_back():
    cfg = load_config("/nonexistent/CONFIG.yaml")
    assert cfg.confidence_threshold == 0.4


def test_load_config_yaml_overrides(tmp_path):
    yaml = __import__("importlib").util.find_spec("yaml")
    if yaml is None:
        import pytest

        pytest.skip("PyYAML not installed")
    cfg_file = tmp_path / "CONFIG.yaml"
    cfg_file.write_text(
        "lae:\n  activation:\n    mode: event_triggered\n"
        "    triggers: [confidence_collapse]\n"
        "    confidence_threshold: 0.7\n    oscillation_window_ms: 500\n"
    )
    cfg = load_config(cfg_file)
    assert cfg.confidence_threshold == 0.7
    assert cfg.oscillation_window_ms == 500
