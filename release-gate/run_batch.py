#!/usr/bin/env python3
"""
Batch evaluation entry point.

Usage:
    python run_batch.py --quick
    python run_batch.py --models gpt-4,claude-3 --scenarios misuse
    python run_batch.py --tag v1.0 --output results/v1
"""

import argparse
from datetime import datetime
from uuid import uuid4

from orchestrator import JobScheduler, Job
from workers import EvalWorker, SimulatedModelClient
from storage import ScenarioDataset, MetricsStore, RunMetadata


def main():
    parser = argparse.ArgumentParser(description='Batch Safeguards Evaluation')
    parser.add_argument('--models', type=str, default='simulated',
                       help='Comma-separated list of models')
    parser.add_argument('--scenarios', type=str, default='all',
                       help='Scenario categories (all, benign, misuse)')
    parser.add_argument('--scenario-version', type=str, default='builtin',
                       help='Scenario dataset version')
    parser.add_argument('--tag', type=str, default='',
                       help='Tag for this run')
    parser.add_argument('--output', type=str, default='results',
                       help='Output directory')
    parser.add_argument('--workers', type=int, default=4,
                       help='Number of worker threads')
    parser.add_argument('--rate-limit', type=float, default=10.0,
                       help='Requests per second limit')
    parser.add_argument('--quick', action='store_true',
                       help='Quick run with minimal scenarios')
    parser.add_argument('-v', '--verbose', action='store_true',
                       help='Verbose output')

    args = parser.parse_args()

    # Parse models
    models = [m.strip() for m in args.models.split(',')]

    # Load scenarios
    dataset = ScenarioDataset()

    if args.scenarios == 'all':
        categories = None
    else:
        categories = [c.strip() for c in args.scenarios.split(',')]

    scenarios = dataset.load_by_category(args.scenario_version, categories)

    if args.quick:
        scenarios = scenarios[:3]

    print("Batch Evaluation")
    print("================")
    print(f"Models: {models}")
    print(f"Scenarios: {len(scenarios)}")
    print(f"Workers: {args.workers}")
    print()

    # Create jobs
    jobs = []
    for model in models:
        for scenario in scenarios:
            job = Job(
                id=f"{model}_{scenario.id}_{uuid4().hex[:8]}",
                model=model,
                scenario_id=scenario.id,
                scenario_data={
                    'id': scenario.id,
                    'category': scenario.category,
                    'name': scenario.name,
                    'request': scenario.request,
                    'turns': scenario.turns,
                    'expected_outcome': scenario.expected_outcome
                }
            )
            jobs.append(job)

    print(f"Created {len(jobs)} jobs")

    # Create worker
    worker = EvalWorker(SimulatedModelClient())

    def worker_fn(job: Job) -> dict:
        return worker.evaluate(job)

    # Run jobs
    scheduler = JobScheduler(
        num_workers=args.workers,
        rate_limit_rps=args.rate_limit
    )
    scheduler.submit_batch(jobs)

    print("Running evaluation...")
    completed_jobs = scheduler.run(worker_fn)

    # Collect results
    results = [job.result for job in completed_jobs if job.result]

    # Compute summary
    total = len(results)
    violations = sum(1 for r in results if r['final_status'] == 'violation')
    hedging = sum(1 for r in results if r['final_status'] == 'hedging')

    print()
    print("Results Summary")
    print("===============")
    print(f"Total: {total}")
    print(f"Violations: {violations} ({violations/total:.1%})")
    print(f"Hedging: {hedging} ({hedging/total:.1%})")
    print(f"Compliant: {total - violations - hedging}")

    # Save results
    run_id = f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    tag = args.tag or run_id

    metadata = RunMetadata(
        run_id=run_id,
        tag=tag,
        models=models,
        scenario_version=args.scenario_version,
        timestamp=datetime.now().isoformat(),
        config={
            'workers': args.workers,
            'rate_limit': args.rate_limit,
            'categories': categories
        }
    )

    store = MetricsStore(base_path=args.output)
    paths = store.save_run(run_id, results, metadata)

    print()
    print("Results saved:")
    for name, path in paths.items():
        print(f"  {name}: {path}")


if __name__ == '__main__':
    main()
