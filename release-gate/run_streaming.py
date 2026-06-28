#!/usr/bin/env python3
"""
Streaming evaluation entry point.

Usage:
    python run_streaming.py --rate 1 --duration 60
    python run_streaming.py --rate 5 --duration 300
"""

import argparse

from streaming import StreamingEvaluator


def main():
    parser = argparse.ArgumentParser(description='Streaming Safeguards Evaluation')
    parser.add_argument('--model', type=str, default='simulated',
                       help='Model to evaluate')
    parser.add_argument('--rate', type=float, default=1.0,
                       help='Requests per second')
    parser.add_argument('--duration', type=int, default=60,
                       help='Duration in seconds (0 = indefinite)')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    print("Streaming Evaluation")
    print("====================")
    print(f"Model: {args.model}")
    print(f"Rate: {args.rate} rps")
    print(f"Duration: {args.duration}s")
    print()

    result_count = 0
    violation_count = 0

    def on_result(result):
        nonlocal result_count, violation_count
        result_count += 1
        if result['final_status'] == 'violation':
            violation_count += 1
        if args.verbose:
            status = result['final_status']
            icon = "🚨" if status == "violation" else "⚠️" if status == "hedging" else "✓"
            print(f"  [{result_count}] {icon} {status}")

    def on_metrics(metrics):
        print(f"\n[Metrics @ {metrics['timestamp']}]")
        print(f"  Requests: {metrics['total_requests']}")
        print(f"  Violation rate: {metrics['violation_rate']:.1%}")
        print(f"  Avg latency: {metrics['avg_latency_ms']:.0f}ms")

    evaluator = StreamingEvaluator(
        model=args.model,
        rate_rps=args.rate,
        on_result=on_result,
        on_metrics=on_metrics
    )

    print("Starting stream...")
    try:
        metrics = evaluator.run_sync(args.duration)
    except KeyboardInterrupt:
        print("\nStopped by user")
        evaluator.stop()
        metrics = evaluator.metrics

    # Final summary
    final = metrics.get_current_metrics()
    print()
    print("Final Summary")
    print("=============")
    print(f"Total requests: {final['total_requests']}")
    print(f"Violation rate: {final['violation_rate']:.1%}")
    print(f"Hedging rate: {final['hedging_rate']:.1%}")
    print(f"Avg latency: {final['avg_latency_ms']:.0f}ms")


if __name__ == '__main__':
    main()
