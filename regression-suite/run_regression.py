#!/usr/bin/env python3
"""
Model Safety Regression Suite - CLI Entry Point

Usage:
    python run_regression.py --quick
    python run_regression.py --baseline model_v1 --candidate model_v2
    python run_regression.py --baseline claude-3.5 --candidate claude-3.6 --report report.html
"""

import argparse
import json
import os

from core import RegressionRunner, DiffEngine, RiskGrader
from reports import HTMLReporter


def main():
    parser = argparse.ArgumentParser(
        description='Model Safety Regression Suite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_regression.py --quick
  python run_regression.py --baseline model_v1 --candidate model_v2
  python run_regression.py --baseline claude-3.5 --candidate claude-3.6 --suite misuse,redteam
        """
    )

    parser.add_argument('--baseline', type=str, help='Baseline model identifier')
    parser.add_argument('--candidate', type=str, help='Candidate model identifier')
    parser.add_argument('--suite', type=str, default='misuse,redteam,trajectory',
                       help='Comma-separated evaluation suites')
    parser.add_argument('--thresholds', type=str, default='configs/thresholds.yaml',
                       help='Path to thresholds YAML')
    parser.add_argument('--report', type=str, help='Output HTML report path')
    parser.add_argument('--json', type=str, help='Output JSON results path')
    parser.add_argument('--quick', action='store_true',
                       help='Quick test with simulated models')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Initialize components
    runner = RegressionRunner()
    diff_engine = DiffEngine()
    risk_grader = RiskGrader(args.thresholds)
    reporter = HTMLReporter()

    print("="*60)
    print("MODEL SAFETY REGRESSION SUITE")
    print("="*60)

    # Run evaluation
    if args.quick:
        print("\nRunning quick test with simulated models...\n")
        run_result = runner.run_quick(verbose=args.verbose)
    else:
        if not args.baseline or not args.candidate:
            parser.error("--baseline and --candidate required (or use --quick)")

        suites = [s.strip() for s in args.suite.split(',')]

        print(f"\nBaseline: {args.baseline}")
        print(f"Candidate: {args.candidate}")
        print(f"Suites: {', '.join(suites)}\n")

        run_result = runner.run(
            baseline_model=args.baseline,
            candidate_model=args.candidate,
            suites=suites,
            verbose=args.verbose
        )

    # Compute diffs
    diffs = diff_engine.compute_diffs(run_result)
    diff_summary = diff_engine.summarize(diffs)

    print(f"\nMetrics analyzed: {diff_summary['total_metrics']}")
    print(f"Regressions: {diff_summary['regressions']}")
    print(f"Improvements: {diff_summary['improvements']}")

    # Grade risk
    risk_report = risk_grader.grade(diffs)
    print(risk_grader.format_verdict(risk_report))

    # Generate HTML report
    if args.report:
        os.makedirs(os.path.dirname(args.report) or '.', exist_ok=True)
        reporter.generate(run_result, diffs, risk_report, args.report)
        print(f"\nHTML report saved to: {args.report}")

    # Save JSON results
    if args.json:
        os.makedirs(os.path.dirname(args.json) or '.', exist_ok=True)
        results = {
            'run': run_result.to_dict(),
            'diffs': [d.to_dict() for d in diffs],
            'risk': risk_report.to_dict()
        }
        with open(args.json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"JSON results saved to: {args.json}")

    # Exit with appropriate code
    if risk_report.verdict.value == 'block':
        exit(1)
    elif risk_report.verdict.value == 'warn':
        exit(2)
    else:
        exit(0)


if __name__ == '__main__':
    main()
