#!/usr/bin/env python3
"""
Agentic Safety Incident Lab - CLI Entry Point

Usage:
    python run_incident.py replay --incident incidents/INC_001.json
    python run_incident.py analyze --incident incidents/INC_001.json
    python run_incident.py blast-radius --incident incidents/INC_001.json
    python run_incident.py generate-regression --incident incidents/INC_001.json
    python run_incident.py full --incident incidents/INC_001.json
"""

import argparse
import json

from incident_replay import IncidentReplayer
from root_cause import RootCauseAnalyzer
from blast_radius import BlastRadiusEstimator
from generate_regression import RegressionGenerator


def cmd_replay(args):
    """Replay an incident."""
    replayer = IncidentReplayer()
    incident = replayer.load_incident(args.incident)
    replayer.replay(incident, with_safeguards=args.with_safeguards)


def cmd_analyze(args):
    """Analyze root cause."""
    analyzer = RootCauseAnalyzer()
    incident = analyzer.load_incident(args.incident)
    analyzer.analyze(incident)


def cmd_blast_radius(args):
    """Estimate blast radius."""
    estimator = BlastRadiusEstimator()
    incident = estimator.load_incident(args.incident)
    estimator.estimate(incident)


def cmd_generate_regression(args):
    """Generate regression test."""
    generator = RegressionGenerator()
    incident = generator.load_incident(args.incident)
    generator.generate(incident, output_dir=args.output)


def cmd_full(args):
    """Run full incident analysis pipeline."""
    print("="*60)
    print("FULL INCIDENT ANALYSIS")
    print("="*60)

    # Load incident once
    with open(args.incident) as f:
        incident = json.load(f)

    incident_id = incident['incident_id']
    print(f"\nIncident: {incident_id}")
    print(f"Title: {incident.get('title', 'Unknown')}")
    print(f"Severity: {incident.get('severity', 'Unknown')}")

    # 1. Replay
    print("\n" + "="*60)
    print("STEP 1: REPLAY")
    print("="*60)
    replayer = IncidentReplayer()
    replayer.replay(incident, with_safeguards=True)

    # 2. Root cause analysis
    print("\n" + "="*60)
    print("STEP 2: ROOT CAUSE ANALYSIS")
    print("="*60)
    analyzer = RootCauseAnalyzer()
    analyzer.analyze(incident)

    # 3. Blast radius
    print("\n" + "="*60)
    print("STEP 3: BLAST RADIUS ESTIMATION")
    print("="*60)
    estimator = BlastRadiusEstimator()
    estimator.estimate(incident)

    # 4. Generate regression
    print("\n" + "="*60)
    print("STEP 4: REGRESSION TEST GENERATION")
    print("="*60)
    generator = RegressionGenerator()
    generator.generate(incident)

    print("\n" + "="*60)
    print("ANALYSIS COMPLETE")
    print("="*60)


def main():
    parser = argparse.ArgumentParser(
        description='Agentic Safety Incident Lab',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Replay command
    replay_parser = subparsers.add_parser('replay', help='Replay an incident')
    replay_parser.add_argument('--incident', required=True, help='Path to incident JSON')
    replay_parser.add_argument('--with-safeguards', action='store_true',
                              help='Simulate with safeguards enabled')
    replay_parser.set_defaults(func=cmd_replay)

    # Analyze command
    analyze_parser = subparsers.add_parser('analyze', help='Analyze root cause')
    analyze_parser.add_argument('--incident', required=True, help='Path to incident JSON')
    analyze_parser.set_defaults(func=cmd_analyze)

    # Blast radius command
    blast_parser = subparsers.add_parser('blast-radius', help='Estimate blast radius')
    blast_parser.add_argument('--incident', required=True, help='Path to incident JSON')
    blast_parser.set_defaults(func=cmd_blast_radius)

    # Generate regression command
    gen_parser = subparsers.add_parser('generate-regression', help='Generate regression test')
    gen_parser.add_argument('--incident', required=True, help='Path to incident JSON')
    gen_parser.add_argument('--output', default='tests/regressions', help='Output directory')
    gen_parser.set_defaults(func=cmd_generate_regression)

    # Full analysis command
    full_parser = subparsers.add_parser('full', help='Run full analysis pipeline')
    full_parser.add_argument('--incident', required=True, help='Path to incident JSON')
    full_parser.set_defaults(func=cmd_full)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    args.func(args)


if __name__ == '__main__':
    main()
