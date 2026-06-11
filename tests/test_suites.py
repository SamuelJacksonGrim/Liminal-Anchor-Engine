"""Pytest wrappers for the narrative check suites.

The suites under tests/smoke/ and tests/integration/ are runnable
diagnostic scripts (python tests/smoke/synthetic_transition.py) that
exit non-zero on failure. These wrappers make them part of the pytest
run so `pytest` alone covers everything.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

SUITES = [
    "tests/smoke/synthetic_transition.py",
    "tests/integration/phase2_phase3.py",
    "tests/integration/phase4_phase5.py",
]


@pytest.mark.parametrize("script", SUITES)
def test_suite_script_passes(script: str):
    proc = subprocess.run(
        [sys.executable, str(REPO_ROOT / script)],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert proc.returncode == 0, (
        f"{script} failed (exit {proc.returncode})\n"
        f"--- stdout (tail) ---\n{proc.stdout[-2000:]}\n"
        f"--- stderr ---\n{proc.stderr[-1000:]}"
    )
