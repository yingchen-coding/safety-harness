"""
Generate regression tests from safety incidents.
"""

import json
import os
import yaml
from dataclasses import dataclass


@dataclass
class RegressionTest:
    """Generated regression test from an incident."""
    id: str
    name: str
    category: str
    source_incident: str
    turns: list[str]
    expected_behavior: dict
    severity: str

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'name': self.name,
            'category': 'regression',
            'source_incident': self.source_incident,
            'turns': self.turns,
            'expected_behavior': self.expected_behavior,
            'severity': self.severity
        }

    def to_yaml(self) -> str:
        return yaml.dump(self.to_dict(), default_flow_style=False, sort_keys=False)


class RegressionGenerator:
    """
    Generates regression tests from incidents for future prevention.
    """

    SAFEGUARD_MAP = {
        'prompt_injection': 'injection_detector',
        'policy_erosion': 'drift_monitor',
        'tool_misuse': 'tool_validator',
        'context_manipulation': 'intent_tracker',
        'coordinated_attack': 'cross_session_analyzer'
    }

    def load_incident(self, path: str) -> dict:
        """Load incident from JSON file."""
        with open(path) as f:
            return json.load(f)

    def generate(
        self,
        incident: dict,
        output_dir: str = 'tests/regressions',
        verbose: bool = True
    ) -> RegressionTest:
        """
        Generate a regression test from an incident.

        Args:
            incident: Incident data
            output_dir: Directory to save test
            verbose: Print output
        """
        incident_id = incident['incident_id']
        failure_type = incident.get('failure_type', 'unknown')
        first_unsafe = incident.get('first_unsafe_turn', -1)
        severity = incident.get('severity', 'medium')

        # Extract turns
        turns = []
        conversation = incident.get('conversation', [])

        # Handle multi-session incidents
        if 'sessions' in incident:
            for session in incident['sessions']:
                for turn in session['conversation']:
                    if turn.get('role') == 'user':
                        turns.append(turn['content'])
        else:
            for turn in conversation:
                if turn.get('role') == 'user':
                    turns.append(turn['content'])

        # Determine expected safeguard
        safeguard = self.SAFEGUARD_MAP.get(failure_type, 'unknown')

        test = RegressionTest(
            id=f"{incident_id}_regression",
            name=f"{incident.get('title', 'Unknown')} (from incident {incident_id})",
            category='regression',
            source_incident=incident_id,
            turns=turns,
            expected_behavior={
                'block_by_turn': first_unsafe if isinstance(first_unsafe, int) else len(turns),
                'trigger_safeguard': safeguard,
                'minimum_action': 'SOFT_STOP'
            },
            severity=severity
        )

        # Save to file
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"{incident_id}.yaml")

        with open(output_path, 'w') as f:
            f.write(f"# Regression test generated from incident {incident_id}\n")
            f.write(f"# {incident.get('title', 'Unknown')}\n\n")
            f.write(test.to_yaml())

        if verbose:
            print(f"Generated regression test: {output_path}")
            print(f"\n{test.to_yaml()}")

        return test


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Generate regression test from incident')
    parser.add_argument('--incident', required=True, help='Path to incident JSON')
    parser.add_argument('--output', default='tests/regressions', help='Output directory')

    args = parser.parse_args()

    generator = RegressionGenerator()
    incident = generator.load_incident(args.incident)
    generator.generate(incident, output_dir=args.output)


if __name__ == '__main__':
    main()
