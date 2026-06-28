#!/usr/bin/env python3
"""
Agentic Safety Demo - Interview-Friendly Mode

One-command demonstration of the complete safety loop:
Discovery -> Conversion -> Gating -> Learning.

Usage:
    python demo.py
    python demo.py --demo-mode
    python demo.py --rollouts 100

The --demo-mode flag produces narrated progress output suitable
for live demonstrations and interviews.
"""

import argparse
import random
import sys
import time
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

from scripts.step1_run_stress_tests import run_redteam
from scripts.step2_generate_regression import generate_tests
from scripts.step3_run_release_gate import run_regression
from scripts.step4_replay_incident import replay_incident, pipeline


def demo_mode_run(rollouts: int = 50, seed: int = 42) -> None:
    """Run demo with narrated progress output."""
    random.seed(seed)
    start_time = time.time()

    artifacts_dir = Path("artifacts")
    artifacts_dir.mkdir(exist_ok=True)

    # Step 1: Stress Testing
    print("[1/4] Running stress tests... ", end="", flush=True)
    stress_report = run_redteam(mode="adaptive", rollouts=rollouts)
    stress_report.save("artifacts/stress_failures.json")
    print(f"Found {stress_report.total_failures} delayed failures (slow-burn vulnerabilities)")

    # Step 2: Regression Generation
    print("[2/4] Converting failures into regressions... ", end="", flush=True)
    suite = generate_tests("artifacts/stress_failures.json")
    suite.save("artifacts/regression_tests.json")
    print(f"Generated {suite.total_tests} new tests")

    # Step 3: Release Gate
    print("[3/4] Running release gate... ", end="", flush=True)
    verdict, _ = run_regression(
        baseline="v1",
        candidate="v2",
        extra_tests="artifacts/regression_tests.json",
        output="artifacts/gate_report.html"
    )
    if verdict == "BLOCK":
        print("BLOCK (safety regression detected)")
    elif verdict == "WARN":
        print("WARN (review recommended)")
    else:
        print("OK (safe to release)")

    # Step 4: Incident Replay
    print("[4/4] Replaying incident INC-2024-001... ", end="", flush=True)
    replay = replay_incident("artifacts/incident_example.json")
    pipeline(replay)
    print(f"{replay.blast_radius:,} conversations affected -> {len(replay.new_tests)} tests promoted")

    elapsed = time.time() - start_time
    print(f"\nDemo completed in {elapsed:.0f}s.")


def standard_run(rollouts: int = 50, seed: int = 42) -> None:
    """Run demo with full output."""
    random.seed(seed)
    start_time = time.time()

    print("=" * 60)
    print("AGENTIC SAFETY DEMO - FULL CLOSED-LOOP SYSTEM")
    print("=" * 60)
    print()
    print("This demo walks through:")
    print("  1. Discovering delayed failures via stress testing")
    print("  2. Converting failures into regression tests")
    print("  3. Gating a candidate model release")
    print("  4. Replaying a production incident")
    print()

    # Step 1
    print("=" * 60)
    print("STEP 1: STRESS TESTING")
    print("=" * 60)
    stress_report = run_redteam(mode="adaptive", rollouts=rollouts)
    stress_report.save("artifacts/stress_failures.json")
    print(f"\nDiscovered {stress_report.total_failures} failures")
    print("Saved to artifacts/stress_failures.json")

    # Step 2
    print()
    print("=" * 60)
    print("STEP 2: REGRESSION TEST GENERATION")
    print("=" * 60)
    suite = generate_tests("artifacts/stress_failures.json")
    suite.save("artifacts/regression_tests.json")
    print(f"\nGenerated {suite.total_tests} tests from {suite.total_failures} failures")
    print("Saved to artifacts/regression_tests.json")

    # Step 3
    print()
    print("=" * 60)
    print("STEP 3: RELEASE GATE")
    print("=" * 60)
    verdict, report_path = run_regression(
        baseline="v1",
        candidate="v2",
        extra_tests="artifacts/regression_tests.json",
        output="artifacts/gate_report.html"
    )
    print(f"\nRelease verdict: {verdict}")
    print(f"Report saved to: {report_path}")

    # Step 4
    print()
    print("=" * 60)
    print("STEP 4: INCIDENT REPLAY")
    print("=" * 60)
    replay = replay_incident("artifacts/incident_example.json")
    pipeline(replay)
    print(f"\nRoot Cause: {replay.root_cause}")
    print(f"Blast Radius: {replay.blast_radius:,} affected conversations")
    print(f"New Regression Tests: {len(replay.new_tests)}")

    elapsed = time.time() - start_time
    print()
    print("=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
    print(f"\nTotal time: {elapsed:.0f} seconds")
    print("\nGenerated artifacts:")
    print("  - artifacts/stress_failures.json")
    print("  - artifacts/regression_tests.json")
    print("  - artifacts/gate_report.html")


def main():
    parser = argparse.ArgumentParser(
        description="Agentic Safety Demo - Closed-Loop Safety System"
    )
    parser.add_argument(
        "--demo-mode",
        action="store_true",
        help="Run in demo mode with narrated progress (interview-friendly)"
    )
    parser.add_argument(
        "--rollouts",
        type=int,
        default=50,
        help="Number of stress test rollouts (default: 50)"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )

    args = parser.parse_args()

    if args.demo_mode:
        demo_mode_run(rollouts=args.rollouts, seed=args.seed)
    else:
        standard_run(rollouts=args.rollouts, seed=args.seed)


if __name__ == "__main__":
    main()
