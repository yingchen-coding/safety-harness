from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    "stress-testing",
    "regression-suite",
    "release-gate",
    "simulator",
    "incident-lab",
    "demo",
)


def test_each_stage_passes_its_local_test_gate() -> None:
    for stage in STAGES:
        stage_dir = ROOT / stage
        env = dict(os.environ)
        env["PYTHONPATH"] = str(stage_dir)
        subprocess.run(
            [sys.executable, "-m", "pytest", "-q"],
            cwd=stage_dir,
            env=env,
            check=True,
        )
