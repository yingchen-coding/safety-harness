#!/usr/bin/env python3
"""
Main entry point for safeguards stress testing.

Usage:
    python run_stress_tests.py                    # Run with defaults
    python run_stress_tests.py --attacks 50      # Run 50 attacks
    python run_stress_tests.py --category jailbreak  # Specific category
    python run_stress_tests.py --plot            # Generate plots
"""

import argparse
import json
import os

from attacks import get_all_attacks, get_attacks_by_category, apply_mutations
from rollout import RolloutEngine, RolloutResult, create_simulated_model
from metrics import compute_metrics, generate_report, save_results


def run_stress_tests(
    categories: list[str] = None,
    n_variants: int = 3,
    max_turns: int = 8,
    task: str = "access restricted information",
    verbose: bool = False,
    failure_prob: float = 0.3
) -> list[RolloutResult]:
    """
    Run stress tests across attack categories.

    Args:
        categories: Attack categories to test (None = all)
        n_variants: Number of mutated variants per attack
        max_turns: Maximum turns per rollout
        task: Task to inject into attack templates
        verbose: Print progress
        failure_prob: Simulated model failure probability

    Returns:
        List of rollout results
    """
    # Get attacks
    if categories:
        attacks = []
        for cat in categories:
            attacks.extend(get_attacks_by_category(cat))
    else:
        attacks = get_all_attacks()

    if verbose:
        print("Running stress tests...")
        print(f"  Attacks: {len(attacks)}")
        print(f"  Variants per attack: {n_variants}")
        print(f"  Max turns: {max_turns}")
        print(f"  Task: {task}")
        print()

    # Create simulated model
    model_fn = create_simulated_model(failure_prob)

    # Create rollout engine
    engine = RolloutEngine(
        model_fn=model_fn,
        verbose=verbose
    )

    results = []

    for i, attack in enumerate(attacks):
        if verbose:
            print(f"[Attack {i+1}/{len(attacks)}] {attack.id}: {attack.name}")

        # Run base attack
        result = engine.run(attack, task=task, max_turns=max_turns)
        results.append(result)

        # Run mutated variants
        for v in range(n_variants - 1):
            # Create mutated version of first turn
            if attack.turns:
                # Apply random mutations
                mutated_attack = type(attack)(
                    id=f"{attack.id}_v{v+1}",
                    category=attack.category,
                    name=f"{attack.name}_variant_{v+1}",
                    turns=attack.turns.copy(),
                    description=attack.description
                )
                # Mutate first turn
                mutations = ["paraphrase", "roleplay", "escalate"]
                import random
                selected = random.sample(mutations, random.randint(1, 2))
                mutated_attack.turns[0] = apply_mutations(
                    attack.turns[0],
                    selected,
                    task=task
                )

                variant_result = engine.run(mutated_attack, task=task, max_turns=max_turns)
                results.append(variant_result)

        if verbose:
            print()

    return results


def generate_plots(metrics, output_dir: str = "results/plots"):
    """Generate visualization plots."""
    os.makedirs(output_dir, exist_ok=True)

    # Try to import matplotlib
    try:
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib not installed. Skipping plots.")
        print("Install with: pip install matplotlib")
        return

    # Erosion curve
    plt.figure(figsize=(10, 6))
    turns = list(range(1, len(metrics.compliance_by_turn) + 1))
    plt.plot(turns, metrics.compliance_by_turn, 'b-o', linewidth=2, markersize=8)
    plt.xlabel('Turn Number', fontsize=12)
    plt.ylabel('Compliance Rate', fontsize=12)
    plt.title('Policy Erosion Curve', fontsize=14)
    plt.ylim(0, 1.05)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, 'erosion_curve.png'), dpi=150)
    plt.close()

    # First failure distribution
    if metrics.first_failure_distribution:
        plt.figure(figsize=(10, 6))
        turns = sorted(metrics.first_failure_distribution.keys())
        counts = [metrics.first_failure_distribution[t] for t in turns]
        plt.bar(turns, counts, color='coral', edgecolor='black')
        plt.xlabel('First Failure Turn', fontsize=12)
        plt.ylabel('Number of Attacks', fontsize=12)
        plt.title('Delayed Failure Distribution', fontsize=14)
        plt.xticks(turns)
        plt.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'delayed_failure_dist.png'), dpi=150)
        plt.close()

    # Success by category
    if metrics.success_by_category:
        plt.figure(figsize=(10, 6))
        categories = list(metrics.success_by_category.keys())
        rates = [metrics.success_by_category[c] for c in categories]
        colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#96ceb4']
        plt.barh(categories, rates, color=colors[:len(categories)], edgecolor='black')
        plt.xlabel('Attack Success Rate', fontsize=12)
        plt.title('Success Rate by Attack Category', fontsize=14)
        plt.xlim(0, 1)
        for i, rate in enumerate(rates):
            plt.text(rate + 0.02, i, f'{rate:.1%}', va='center')
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'success_by_category.png'), dpi=150)
        plt.close()

    print(f"Plots saved to: {output_dir}/")


def main():
    parser = argparse.ArgumentParser(description='Safeguards Stress Tests')
    parser.add_argument('--category', type=str, nargs='+',
                       help='Attack categories to test',
                       choices=['jailbreak', 'decomposition', 'tool_hallucination', 'context_manipulation'])
    parser.add_argument('--variants', type=int, default=3,
                       help='Number of variants per attack')
    parser.add_argument('--turns', type=int, default=8,
                       help='Maximum turns per rollout')
    parser.add_argument('--task', type=str, default='access restricted information',
                       help='Task to inject into attacks')
    parser.add_argument('--failure-prob', type=float, default=0.3,
                       help='Simulated model failure probability')
    parser.add_argument('--output', type=str, default='results/raw.jsonl',
                       help='Output file for raw results')
    parser.add_argument('--plot', action='store_true',
                       help='Generate visualization plots')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Run tests
    results = run_stress_tests(
        categories=args.category,
        n_variants=args.variants,
        max_turns=args.turns,
        task=args.task,
        verbose=args.verbose,
        failure_prob=args.failure_prob
    )

    # Compute metrics
    metrics = compute_metrics(results)

    # Print report
    print(generate_report(metrics))

    # Save results
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    save_results(results, args.output)
    print(f"\nRaw results saved to: {args.output}")

    # Generate plots
    if args.plot:
        generate_plots(metrics)

    # Save metrics summary
    metrics_file = args.output.replace('.jsonl', '_metrics.json')
    with open(metrics_file, 'w') as f:
        json.dump(metrics.to_dict(), f, indent=2)
    print(f"Metrics saved to: {metrics_file}")


if __name__ == '__main__':
    main()
