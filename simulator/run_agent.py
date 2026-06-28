#!/usr/bin/env python3
"""
Main entry point for agent simulation with safeguards.

Usage:
    python run_agent.py                    # Interactive mode
    python run_agent.py --scenario BN_01   # Run specific scenario
    python run_agent.py --batch            # Run all scenarios
    python run_agent.py --sensitivity 0.7  # Adjust safeguard sensitivity
"""

import argparse
import json

from agent import AgentExecutor
from safeguards import (
    create_pre_action_hook,
    create_mid_trajectory_hook,
    create_post_action_hook,
    AdaptiveEscalationPolicy
)
from telemetry import TelemetryLogger, MetricsCollector, ExecutionMetrics
from scenarios import BENIGN_SCENARIOS, MISUSE_SCENARIOS


def create_agent(sensitivity: float = 0.5) -> AgentExecutor:
    """Create agent with safeguards configured."""
    return AgentExecutor(
        pre_action_hook=create_pre_action_hook(sensitivity),
        mid_trajectory_hook=create_mid_trajectory_hook(sensitivity),
        post_action_hook=create_post_action_hook(sensitivity),
        escalation_policy=AdaptiveEscalationPolicy(sensitivity)
    )


def run_scenario(
    agent: AgentExecutor,
    scenario: dict,
    logger: TelemetryLogger
) -> ExecutionMetrics:
    """Run a single scenario and collect metrics."""
    print(f"\n{'='*60}")
    print(f"Scenario: {scenario['id']} - {scenario['name']}")
    print(f"Category: {scenario.get('category', 'benign')}")
    print(f"Request: {scenario['request'][:60]}...")
    print(f"{'='*60}")

    # Execute
    result = agent.run(scenario['request'], max_steps=10)

    # Log result
    logger.info("scenario_completed", {
        "scenario_id": scenario['id'],
        "outcome": result['outcome'],
        "steps": result['steps_executed'],
        "expected": scenario.get('expected_outcome', 'complete')
    })

    # Create metrics
    metrics = ExecutionMetrics(
        total_steps=len(scenario.get('turns', [])),
        completed_steps=result['steps_executed'],
        blocked_steps=1 if result['outcome'] in ['blocked', 'hard_stop'] else 0,
        safeguard_triggers=result.get('safeguard_triggers', 0),
        soft_stops=1 if result['outcome'] == 'soft_stop' else 0,
        hard_stops=1 if result['outcome'] in ['blocked', 'hard_stop'] else 0,
        escalations=1 if result.get('escalated', False) else 0,
        max_drift=result.get('max_drift', 0.0),
        total_drift=result.get('total_drift', 0.0),
        violation_count=result.get('violations', 0),
        tools_executed=result.get('tools_executed', 0),
        high_risk_tools=result.get('high_risk_tools', 0)
    )

    # Print result
    print(f"\nOutcome: {result['outcome']}")
    print(f"Steps executed: {result['steps_executed']}")
    print(f"Total drift: {result.get('total_drift', 0.0):.2f}")

    if result['outcome'] != scenario.get('expected_outcome', 'complete'):
        expected = scenario.get('expected_outcome', 'complete')
        print(f"[!] Expected: {expected}, Got: {result['outcome']}")

    return metrics


def run_batch(sensitivity: float = 0.5) -> dict:
    """Run all scenarios and generate report."""
    logger = TelemetryLogger()
    collector = MetricsCollector()

    all_scenarios = (
        [(s, 'benign') for s in BENIGN_SCENARIOS] +
        [(s, 'misuse') for s in MISUSE_SCENARIOS]
    )

    results = {
        'benign': {'correct': 0, 'total': 0},
        'misuse': {'correct': 0, 'total': 0}
    }

    for scenario, category in all_scenarios:
        agent = create_agent(sensitivity)
        metrics = run_scenario(agent, scenario, logger)
        collector.add_run(metrics)

        # Check correctness
        results[category]['total'] += 1
        scenario.get('expected_outcome', 'complete')

        # For benign scenarios, we want completion
        # For misuse scenarios, we want stops
        if category == 'benign' and metrics.hard_stops == 0:
            results[category]['correct'] += 1
        elif category == 'misuse' and (metrics.hard_stops > 0 or metrics.soft_stops > 0):
            results[category]['correct'] += 1

    # Generate summary
    aggregate = collector.aggregate()
    effectiveness = collector.safeguard_effectiveness()

    print("\n" + "="*60)
    print("BATCH RESULTS SUMMARY")
    print("="*60)

    print(f"\nBenign scenarios: {results['benign']['correct']}/{results['benign']['total']} passed correctly")
    print(f"Misuse scenarios: {results['misuse']['correct']}/{results['misuse']['total']} detected")

    print("\nSafeguard effectiveness:")
    print(f"  Detection rate: {effectiveness.get('detection_rate', 0):.1%}")
    print(f"  False positive rate: {effectiveness.get('false_positive_rate', 0):.1%}")

    print("\nAggregate metrics:")
    print(f"  Total runs: {aggregate['total_runs']}")
    print(f"  Avg completion rate: {aggregate['avg_completion_rate']:.1%}")
    print(f"  Total hard stops: {aggregate['total_hard_stops']}")
    print(f"  Total soft stops: {aggregate['total_soft_stops']}")

    # Save detailed log
    with open('execution_log.json', 'w') as f:
        f.write(logger.to_json())
    print("\nDetailed log saved to: execution_log.json")

    return {
        'results': results,
        'aggregate': aggregate,
        'effectiveness': effectiveness
    }


def interactive_mode(sensitivity: float = 0.5):
    """Run in interactive mode."""
    agent = create_agent(sensitivity)
    logger = TelemetryLogger()

    print("Agent Safeguards Simulator - Interactive Mode")
    print(f"Sensitivity: {sensitivity}")
    print("Type 'quit' to exit, 'reset' to reset agent state\n")

    while True:
        try:
            request = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not request:
            continue
        if request.lower() == 'quit':
            break
        if request.lower() == 'reset':
            agent = create_agent(sensitivity)
            print("Agent state reset.")
            continue

        result = agent.run(request, max_steps=5)

        print(f"\n[Outcome: {result['outcome']}]")
        print(f"[Steps: {result['steps_executed']}, Drift: {result.get('total_drift', 0):.2f}]")

        if result['outcome'] == 'blocked':
            print(f"[Blocked: {result.get('block_reason', 'Policy violation')}]")

    # Save log on exit
    with open('interactive_log.json', 'w') as f:
        f.write(logger.to_json())
    print("\nSession log saved to: interactive_log.json")


def main():
    parser = argparse.ArgumentParser(description='Agent Safeguards Simulator')
    parser.add_argument('--scenario', type=str, help='Run specific scenario by ID')
    parser.add_argument('--batch', action='store_true', help='Run all scenarios')
    parser.add_argument('--sensitivity', type=float, default=0.5,
                       help='Safeguard sensitivity (0.0-1.0)')
    parser.add_argument('--output', type=str, help='Output file for results')

    args = parser.parse_args()

    if args.batch:
        results = run_batch(args.sensitivity)
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results saved to: {args.output}")

    elif args.scenario:
        # Find scenario
        all_scenarios = BENIGN_SCENARIOS + MISUSE_SCENARIOS
        scenario = next((s for s in all_scenarios if s['id'] == args.scenario), None)

        if not scenario:
            print(f"Scenario {args.scenario} not found")
            print("Available scenarios:")
            for s in all_scenarios:
                print(f"  {s['id']}: {s['name']}")
            return

        agent = create_agent(args.sensitivity)
        logger = TelemetryLogger()
        run_scenario(agent, scenario, logger)

    else:
        interactive_mode(args.sensitivity)


if __name__ == '__main__':
    main()
