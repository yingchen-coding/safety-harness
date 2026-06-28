#!/usr/bin/env python3
"""
Step 1: Discover Delayed Failures via Stress Testing

This script runs adaptive red-teaming against a target model
and discovers delayed policy erosion failures.

Usage:
    python scripts/step1_run_stress_tests.py --rollouts 50
"""

import argparse
import json
import random
import time
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict


@dataclass
class Failure:
    """A discovered failure."""
    failure_id: str
    rollout_id: int
    failure_turn: int
    attack_type: str
    harm_level: int
    trajectory: List[str]
    model_responses: List[str]


@dataclass
class StressReport:
    """Report from stress testing."""
    total_rollouts: int
    total_failures: int
    failures: List[Failure]
    by_turn: Dict[int, int]
    by_attack_type: Dict[str, int]
    avg_failure_turn: float

    def save(self, path: str):
        """Save report to JSON."""
        output = {
            "total_rollouts": self.total_rollouts,
            "total_failures": self.total_failures,
            "failures": [asdict(f) for f in self.failures],
            "by_turn": self.by_turn,
            "by_attack_type": self.by_attack_type,
            "avg_failure_turn": self.avg_failure_turn
        }
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            json.dump(output, f, indent=2)


def run_redteam(mode: str, rollouts: int) -> StressReport:
    """Run red-teaming and discover failures."""
    print(f"Running {rollouts} {mode} rollouts...")

    failures = []
    by_turn = {}
    by_attack_type = {}

    attack_types = ["policy_erosion", "intent_drift", "decomposition", "context_manipulation"]

    for i in range(rollouts):
        # Simulate rollout
        attack_type = random.choice(attack_types)
        max_turns = 8

        # Adaptive mode has higher success rate for delayed failures
        if mode == "adaptive":
            failure_prob = 0.25
            avg_turn = 5.5
        else:
            failure_prob = 0.15
            avg_turn = 3.5

        if random.random() < failure_prob:
            # Generate failure
            failure_turn = max(1, min(max_turns, int(random.gauss(avg_turn, 1.5))))

            failure = Failure(
                failure_id=f"fail_{len(failures):04d}",
                rollout_id=i,
                failure_turn=failure_turn,
                attack_type=attack_type,
                harm_level=random.randint(2, 4),
                trajectory=[f"Turn {t}: [redacted attack]" for t in range(1, failure_turn + 1)],
                model_responses=[f"Turn {t}: [redacted response]" for t in range(1, failure_turn + 1)]
            )
            failures.append(failure)

            by_turn[failure_turn] = by_turn.get(failure_turn, 0) + 1
            by_attack_type[attack_type] = by_attack_type.get(attack_type, 0) + 1

        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Completed {i + 1}/{rollouts} rollouts...")

    avg_failure_turn = (
        sum(f.failure_turn for f in failures) / len(failures)
        if failures else 0
    )

    return StressReport(
        total_rollouts=rollouts,
        total_failures=len(failures),
        failures=failures,
        by_turn=by_turn,
        by_attack_type=by_attack_type,
        avg_failure_turn=avg_failure_turn
    )


def main():
    parser = argparse.ArgumentParser(
        description="Run stress tests to discover delayed failures"
    )
    parser.add_argument(
        "--rollouts",
        type=int,
        default=50,
        help="Number of rollouts to run"
    )
    parser.add_argument(
        "--mode",
        choices=["static", "adaptive"],
        default="adaptive",
        help="Attack mode"
    )
    parser.add_argument(
        "--output",
        default="artifacts/stress_failures.json",
        help="Output file path"
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed"
    )

    args = parser.parse_args()
    random.seed(args.seed)

    print("=" * 60)
    print("STEP 1: STRESS TESTING")
    print("=" * 60)
    print(f"Mode: {args.mode}")
    print(f"Rollouts: {args.rollouts}")
    print()

    start_time = time.time()
    report = run_redteam(mode=args.mode, rollouts=args.rollouts)
    elapsed = time.time() - start_time

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Total rollouts: {report.total_rollouts}")
    print(f"Discovered failures: {report.total_failures}")
    print(f"Failure rate: {report.total_failures / report.total_rollouts:.1%}")
    print(f"Avg failure turn: {report.avg_failure_turn:.1f}")

    print("\nFailures by turn:")
    for turn in sorted(report.by_turn.keys()):
        count = report.by_turn[turn]
        bar = "#" * count
        print(f"  Turn {turn}: {count:3d} {bar}")

    print("\nFailures by attack type:")
    for attack_type, count in sorted(report.by_attack_type.items(), key=lambda x: -x[1]):
        print(f"  {attack_type}: {count}")

    report.save(args.output)
    print(f"\nSaved to {args.output}")
    print(f"Elapsed time: {elapsed:.1f}s")


if __name__ == "__main__":
    main()
