#!/usr/bin/env python3
"""
Step 6: Show Executive Safety Dashboard

Copies the unified executive dashboard from regression-suite
to demo artifacts for presentation.

Usage:
    python scripts/step6_show_exec_dashboard.py
"""

import shutil
import subprocess
from pathlib import Path

DEMO_ROOT = Path(__file__).resolve().parents[1]
REGRESSION_SUITE = DEMO_ROOT.parent / "model-safety-regression-suite"

SRC = REGRESSION_SUITE / "artifacts" / "executive_safety_dashboard.html"
ROI_SRC = REGRESSION_SUITE / "artifacts" / "safety_roi_model.json"
DST = DEMO_ROOT / "artifacts"


def generate_dashboard():
    """Generate executive dashboard in regression suite."""
    print("\n[Step 6a] Generating Executive Dashboard...")

    # First generate ROI model
    roi_script = REGRESSION_SUITE / "scripts" / "generate_safety_roi_model.py"
    if roi_script.exists():
        print("  Running: generate_safety_roi_model.py")
        subprocess.run(["python", str(roi_script)], cwd=REGRESSION_SUITE)

    # Then generate dashboard
    dashboard_script = REGRESSION_SUITE / "scripts" / "generate_executive_dashboard.py"
    if dashboard_script.exists():
        print("  Running: generate_executive_dashboard.py")
        subprocess.run(["python", str(dashboard_script)], cwd=REGRESSION_SUITE)


def copy_dashboard():
    """Copy dashboard to demo."""
    print("\n[Step 6b] Copying Executive Dashboard to Demo...")

    copied = 0

    if SRC.exists():
        shutil.copy(SRC, DST / "executive_safety_dashboard.html")
        print("  Copied: executive_safety_dashboard.html")
        copied += 1
    else:
        print(f"  Not found: {SRC}")

    if ROI_SRC.exists():
        shutil.copy(ROI_SRC, DST / "safety_roi_model.json")
        print("  Copied: safety_roi_model.json")
        copied += 1

    return copied


def main():
    print("=" * 60)
    print("STEP 6: EXECUTIVE SAFETY DASHBOARD")
    print("=" * 60)
    print("\nGenerating board-meeting-ready artifact...")

    generate_dashboard()
    copied = copy_dashboard()

    print("\n" + "=" * 60)
    print("[OK] Executive Dashboard ready: artifacts/executive_safety_dashboard.html")
    print("[OK] ROI Model: artifacts/safety_roi_model.json")
    print("=" * 60)

    if copied > 0:
        print("\n💰 This dashboard is ready for board presentation.")
        print("   It includes ROI framing for safety investments.")


if __name__ == "__main__":
    main()
