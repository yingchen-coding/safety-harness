#!/usr/bin/env python3
"""
Release gate entry point.

Usage:
    python run_release_gate.py --baseline v1.0 --candidate v1.1
    python run_release_gate.py --candidate v1.1  # No baseline comparison

Exit codes:
    0 = OK (release allowed)
    1 = WARN (release allowed with warnings)
    2 = BLOCK (release blocked)
"""

import argparse
import sys

from core.release_gate import ReleaseGateEngine, VersionInfo, GateDecision
from storage import MetricsStore


def main():
    parser = argparse.ArgumentParser(description='Release Gate Evaluation')
    parser.add_argument('--baseline', type=str, help='Baseline run ID for comparison')
    parser.add_argument('--candidate', type=str, required=True, help='Candidate run ID to evaluate')
    parser.add_argument('--output', type=str, default='results', help='Results directory')
    parser.add_argument('--config', type=str, default='config/release_gate.yaml',
                       help='Gate configuration file')
    parser.add_argument('--json', action='store_true', help='Output JSON format')
    parser.add_argument('--model-version', type=str, default='unknown',
                       help='Model version for tracking')
    parser.add_argument('--safeguard-version', type=str, default='unknown',
                       help='Safeguard version for tracking')
    parser.add_argument('--attack-suite', type=str, default='unknown',
                       help='Attack suite version for tracking')
    parser.add_argument('--benchmark-version', type=str, default='unknown',
                       help='Benchmark version for tracking')

    args = parser.parse_args()

    # Load metrics
    store = MetricsStore(base_path=args.output)

    try:
        candidate_summary = store.compute_summary(args.candidate)
    except Exception as e:
        print(f"Error loading candidate run: {e}", file=sys.stderr)
        sys.exit(2)

    baseline_summary = None
    if args.baseline:
        try:
            baseline_summary = store.compute_summary(args.baseline)
        except Exception as e:
            print(f"Warning: Could not load baseline run: {e}", file=sys.stderr)

    # Convert summary to metrics dict
    candidate_metrics = {
        'failure_rate': candidate_summary.get('violation_rate', 0),
        'avg_first_failure': candidate_summary.get('avg_first_failure_turn'),
        'avg_latency_ms': candidate_summary.get('avg_latency_ms', 0),
    }

    baseline_metrics = None
    if baseline_summary:
        baseline_metrics = {
            'failure_rate': baseline_summary.get('violation_rate', 0),
            'avg_first_failure': baseline_summary.get('avg_first_failure_turn'),
            'avg_latency_ms': baseline_summary.get('avg_latency_ms', 0),
        }

    # Run gate evaluation
    engine = ReleaseGateEngine(config_path=args.config)
    versions = VersionInfo(
        model_version=args.model_version,
        safeguard_version=args.safeguard_version,
        attack_suite=args.attack_suite,
        benchmark_version=args.benchmark_version
    )

    result = engine.evaluate(
        run_id=f"{args.candidate}_gate",
        versions=versions,
        candidate_metrics=candidate_metrics,
        baseline_metrics=baseline_metrics
    )

    # Output result
    if args.json:
        print(result.to_json())
    else:
        print()
        print("Release Gate Result")
        print("=" * 50)
        print(f"Run ID: {result.run_id}")
        print(f"Timestamp: {result.timestamp}")
        print()
        print(f"Gate Decision: {result.gate_decision.value}")
        print()
        if result.reasons:
            print("Reasons:")
            for reason in result.reasons:
                print(f"  - {reason}")
        print()
        print(f"Regression Severity: {result.regression_severity:.2f}")
        print(f"Safety Budget Remaining: {result.safety_budget_remaining:.1%}")
        print()
        if result.regressions:
            print("Regressions:")
            for reg in result.regressions:
                print(f"  {reg.metric}: {reg.baseline:.3f} -> {reg.candidate:.3f} ({reg.status})")

    # Exit with appropriate code
    if result.gate_decision == GateDecision.OK:
        sys.exit(0)
    elif result.gate_decision == GateDecision.WARN:
        sys.exit(1)
    else:  # BLOCK
        sys.exit(2)


if __name__ == '__main__':
    main()
