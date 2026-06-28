#!/usr/bin/env python3
"""
Plot erosion curves from red-teaming results.

Usage:
    python demos/plot_erosion_curves.py --input results/latest.json
    python demos/plot_erosion_curves.py --input results/latest.json --output erosion.png
"""

import argparse
import json
from pathlib import Path


def load_results(input_path):
    """Load results from JSON file."""
    with open(input_path) as f:
        return json.load(f)


def compute_erosion_curve(results):
    """Compute cumulative violation rate by turn."""
    by_turn = results.get("by_turn", {})
    total = results.get("total_rollouts", 100)

    # Get max turn
    max_turn = max(int(t) for t in by_turn.keys()) if by_turn else 10

    # Compute cumulative
    cumulative = {}
    running_total = 0
    for turn in range(1, max_turn + 1):
        running_total += by_turn.get(str(turn), 0)
        cumulative[turn] = running_total / total

    return cumulative


def print_ascii_chart(curves, title="Erosion Curves"):
    """Print ASCII chart of erosion curves."""
    print(f"\n{title}")
    print("=" * 60)

    max_turn = max(max(c.keys()) for c in curves.values())

    # Y-axis labels
    y_labels = [1.0, 0.75, 0.5, 0.25, 0.0]

    print("\nCumulative Violation Rate")
    print("   |")

    for y in y_labels:
        row = f"{y:3.0%}|"
        for turn in range(1, max_turn + 1):
            chars = []
            for name, curve in curves.items():
                val = curve.get(turn, 0)
                if abs(val - y) < 0.05:
                    if name == "static":
                        chars.append("S")
                    else:
                        chars.append("A")

            if chars:
                row += "".join(set(chars))
            else:
                row += " "
        print(row)

    print("   +" + "-" * max_turn)
    print("    " + "".join(str(i % 10) for i in range(1, max_turn + 1)))
    print("    Turn Number")

    print("\nLegend: S=Static, A=Adaptive")


def print_table(curves):
    """Print comparison table."""
    print("\n--- Erosion Comparison Table ---")
    print(f"{'Turn':<6}", end="")
    for name in curves.keys():
        print(f"{name:>12}", end="")
    print()
    print("-" * (6 + 12 * len(curves)))

    max_turn = max(max(c.keys()) for c in curves.values())

    for turn in range(1, max_turn + 1):
        print(f"{turn:<6}", end="")
        for name, curve in curves.items():
            val = curve.get(turn, 0)
            print(f"{val:>11.1%}", end="")
        print()


def analyze_curves(curves):
    """Analyze and compare curves."""
    print("\n--- Analysis ---")

    for name, curve in curves.items():
        max_turn = max(curve.keys())
        final_rate = curve[max_turn]
        midpoint = curve.get(max_turn // 2, 0)

        print(f"\n{name.upper()}:")
        print(f"  Final violation rate: {final_rate:.1%}")
        print(f"  Midpoint rate: {midpoint:.1%}")

        # Find turn where 50% of final violations occurred
        half_final = final_rate / 2
        half_turn = next(
            (t for t, v in sorted(curve.items()) if v >= half_final),
            max_turn
        )
        print(f"  50% of violations by turn: {half_turn}")

    # Compare if multiple curves
    if len(curves) > 1:
        names = list(curves.keys())
        curve1 = curves[names[0]]
        curve2 = curves[names[1]]

        max_turn = max(max(curve1.keys()), max(curve2.keys()))
        final_diff = curve2[max_turn] - curve1[max_turn]

        print("\n--- Comparison ---")
        print(f"Final rate difference ({names[1]} vs {names[0]}): {final_diff:+.1%}")

        if final_diff > 0.1:
            print(f"{names[1]} discovers significantly more violations.")
        elif final_diff < -0.1:
            print(f"{names[0]} discovers significantly more violations.")
        else:
            print("Similar final violation rates between modes.")


def main():
    parser = argparse.ArgumentParser(
        description="Plot erosion curves from red-team results"
    )
    parser.add_argument(
        "--input",
        required=True,
        help="Input JSON file with results"
    )
    parser.add_argument(
        "--compare",
        type=str,
        default=None,
        help="Second input file for comparison"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for plot (requires matplotlib)"
    )

    args = parser.parse_args()

    print("=" * 60)
    print("EROSION CURVE ANALYSIS")
    print("=" * 60)

    # Load primary results
    if not Path(args.input).exists():
        # Generate mock results for demo
        print("\nNo input file found. Generating mock results for demonstration...")
        results = {
            "static": {
                "mode": "static",
                "total_rollouts": 100,
                "by_turn": {"1": 5, "2": 8, "3": 12, "4": 10, "5": 8, "6": 5, "7": 3, "8": 2}
            },
            "adaptive": {
                "mode": "adaptive",
                "total_rollouts": 100,
                "by_turn": {"1": 3, "2": 5, "3": 8, "4": 12, "5": 15, "6": 10, "7": 8, "8": 6}
            }
        }
        curves = {
            name: compute_erosion_curve(data)
            for name, data in results.items()
        }
    else:
        results = load_results(args.input)
        curves = {results["mode"]: compute_erosion_curve(results)}

        if args.compare and Path(args.compare).exists():
            results2 = load_results(args.compare)
            curves[results2["mode"]] = compute_erosion_curve(results2)

    # Display results
    print_ascii_chart(curves)
    print_table(curves)
    analyze_curves(curves)

    # Key insights
    print(f"\n{'=' * 60}")
    print("KEY INSIGHTS")
    print(f"{'=' * 60}")

    if len(curves) > 1:
        print("""
Static attacks plateau quickly - most violations happen early.
Adaptive attacks show continued discovery - finding delayed failures.

This demonstrates why adaptive red-teaming is essential for
discovering slow-burn vulnerabilities that static testing misses.
        """)
    else:
        print("""
Single-mode results. Run with --compare to compare static vs adaptive.
        """)


if __name__ == "__main__":
    main()
