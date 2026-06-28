#!/usr/bin/env python3
"""
Compare evaluation runs for regression detection.

Usage:
    python compare_runs.py --baseline run_001 --candidate run_002
    python compare_runs.py --list
"""

import argparse

from storage import MetricsStore


def main():
    parser = argparse.ArgumentParser(description='Compare Evaluation Runs')
    parser.add_argument('--baseline', type=str, help='Baseline run ID')
    parser.add_argument('--candidate', type=str, help='Candidate run ID')
    parser.add_argument('--list', action='store_true', help='List available runs')
    parser.add_argument('--output', type=str, default='results',
                       help='Results directory')

    args = parser.parse_args()

    store = MetricsStore(base_path=args.output)

    if args.list:
        runs = store.list_runs()
        print(f"Available runs ({len(runs)}):")
        for run in runs:
            try:
                summary = store.compute_summary(run)
                print(f"  {run}: {summary['total_scenarios']} scenarios, "
                      f"{summary['violation_rate']:.1%} violation rate")
            except Exception:
                print(f"  {run}: (error loading)")
        return

    if not args.baseline or not args.candidate:
        parser.error("--baseline and --candidate required for comparison")

    # Load summaries
    try:
        base_summary = store.compute_summary(args.baseline)
        cand_summary = store.compute_summary(args.candidate)
    except Exception as e:
        print(f"Error loading runs: {e}")
        return

    # Compare
    print()
    print(f"Regression Report: {args.baseline} → {args.candidate}")
    print("=" * 60)

    metrics = [
        ('violation_rate', 'Violation Rate', lambda x: f"{x:.1%}", True),
        ('avg_first_failure_turn', 'Avg First Failure Turn', lambda x: f"{x:.2f}" if x else "N/A", False),
        ('avg_latency_ms', 'Avg Latency (ms)', lambda x: f"{x:.0f}", True),
    ]

    print(f"{'Metric':<25} {'Baseline':<12} {'Candidate':<12} {'Delta':<10} Status")
    print("-" * 60)

    regressions = 0

    for key, name, fmt, higher_is_worse in metrics:
        base_val = base_summary.get(key)
        cand_val = cand_summary.get(key)

        if base_val is None or cand_val is None:
            status = "⚪ N/A"
            delta_str = "N/A"
        else:
            delta = cand_val - base_val

            if key == 'violation_rate':
                delta_str = f"{delta:+.1%}"
            else:
                delta_str = f"{delta:+.2f}"

            # Determine regression
            threshold = 0.02 if key == 'violation_rate' else (base_val * 0.1 if base_val else 0.5)

            if higher_is_worse:
                if delta > threshold:
                    status = "🔴 REGRESSION"
                    regressions += 1
                elif delta < -threshold:
                    status = "🟢 IMPROVED"
                else:
                    status = "⚪ STABLE"
            else:
                if delta < -threshold:
                    status = "🔴 REGRESSION"
                    regressions += 1
                elif delta > threshold:
                    status = "🟢 IMPROVED"
                else:
                    status = "⚪ STABLE"

        base_str = fmt(base_val) if base_val is not None else "N/A"
        cand_str = fmt(cand_val) if cand_val is not None else "N/A"

        print(f"{name:<25} {base_str:<12} {cand_str:<12} {delta_str:<10} {status}")

    print("-" * 60)

    if regressions > 0:
        print(f"\n⚠️  {regressions} regression(s) detected!")
    else:
        print("\n✅ No regressions detected.")


if __name__ == '__main__':
    main()
