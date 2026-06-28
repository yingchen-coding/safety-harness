"""
Incident replay engine for reproducing safety failures.
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ReplayResult:
    """Result from incident replay."""
    incident_id: str
    total_turns: int
    first_unsafe_turn: int
    turn_statuses: list[dict]
    safeguard_analysis: Optional[dict]
    prevention_estimate: Optional[float]

    def to_dict(self) -> dict:
        return {
            'incident_id': self.incident_id,
            'total_turns': self.total_turns,
            'first_unsafe_turn': self.first_unsafe_turn,
            'turn_statuses': self.turn_statuses,
            'safeguard_analysis': self.safeguard_analysis,
            'prevention_estimate': self.prevention_estimate
        }


class IncidentReplayer:
    """
    Replays incidents to understand failure progression.
    """

    STATUS_ICONS = {
        'safe': '✓',
        'hedge': '⚠️',
        'unsafe': '🚨'
    }

    def __init__(self):
        pass

    def load_incident(self, path: str) -> dict:
        """Load incident from JSON file."""
        with open(path) as f:
            return json.load(f)

    def replay(
        self,
        incident: dict,
        with_safeguards: bool = False,
        verbose: bool = True
    ) -> ReplayResult:
        """
        Replay an incident turn by turn.

        Args:
            incident: Incident data
            with_safeguards: Simulate with safeguards enabled
            verbose: Print replay output
        """
        incident_id = incident['incident_id']

        # Support both 'trajectory' and 'conversation' keys
        conversation = incident.get('trajectory', incident.get('conversation', []))

        # Handle multi-session incidents
        if 'sessions' in incident:
            conversation = []
            for session in incident['sessions']:
                for turn in session['conversation']:
                    turn['session'] = session['session_id']
                    conversation.append(turn)

        first_unsafe = incident.get('first_unsafe_turn', -1)
        if isinstance(first_unsafe, str):
            # Handle "sess_D:4" format
            first_unsafe = len(conversation)

        turn_statuses = []

        if verbose:
            print(f"\n{'='*60}")
            print(f"INCIDENT REPLAY: {incident_id}")
            print(f"{incident.get('title', 'Unknown')}")
            print(f"{'='*60}\n")

        for i, turn in enumerate(conversation):
            turn_num = turn.get('turn', i + 1)
            role = turn.get('role', 'unknown')
            content = turn.get('content', '')[:60]
            # Derive status from violation field if status not present
            if 'status' in turn:
                status = turn['status']
            elif turn.get('violation', False):
                status = 'unsafe'
            else:
                status = 'safe'

            self.STATUS_ICONS.get(status, '?')

            turn_statuses.append({
                'turn': turn_num,
                'role': role,
                'status': status,
                'content_preview': content
            })

            if verbose and role == 'assistant':
                marker = ' ← FAILURE POINT' if turn_num == first_unsafe else ''
                print(f"Turn {turn_num}: [{status.upper()}] \"{content}...\"{marker}")

        # Simulate safeguard analysis
        safeguard_analysis = None
        prevention_estimate = None

        if with_safeguards:
            safeguard_analysis = self._simulate_safeguards(incident)
            prevention_estimate = self._estimate_prevention(incident)

            if verbose:
                print("\nWith safeguards:")
                print(f"  Would trigger: {safeguard_analysis.get('would_trigger', 'unknown')}")
                print(f"  At turn: {safeguard_analysis.get('trigger_turn', 'N/A')}")
                print(f"  Estimated prevention: {prevention_estimate:.0%}")

        return ReplayResult(
            incident_id=incident_id,
            total_turns=len(conversation),
            first_unsafe_turn=first_unsafe,
            turn_statuses=turn_statuses,
            safeguard_analysis=safeguard_analysis,
            prevention_estimate=prevention_estimate
        )

    def _simulate_safeguards(self, incident: dict) -> dict:
        """Simulate what safeguards would have done."""
        failure_type = incident.get('failure_type', 'unknown')
        first_unsafe = incident.get('first_unsafe_turn', -1)

        safeguard_map = {
            'prompt_injection': ('pre_action', 'injection_detector'),
            'policy_erosion': ('mid_trajectory', 'drift_monitor'),
            'tool_misuse': ('pre_action', 'tool_validator'),
            'context_manipulation': ('mid_trajectory', 'intent_tracker'),
            'coordinated_attack': ('cross_session', 'pattern_analyzer')
        }

        hook, safeguard = safeguard_map.get(failure_type, ('unknown', 'unknown'))

        return {
            'would_trigger': f'{hook}: {safeguard}',
            'trigger_turn': max(1, first_unsafe - 1) if isinstance(first_unsafe, int) else 'N/A',
            'action': 'SOFT_STOP' if failure_type in ['policy_erosion', 'context_manipulation'] else 'HARD_STOP'
        }

    def _estimate_prevention(self, incident: dict) -> float:
        """Estimate prevention probability with safeguards."""
        failure_type = incident.get('failure_type', 'unknown')

        # Estimated prevention rates by failure type
        prevention_rates = {
            'prompt_injection': 0.92,
            'policy_erosion': 0.78,
            'tool_misuse': 0.85,
            'context_manipulation': 0.65,
            'coordinated_attack': 0.45
        }

        return prevention_rates.get(failure_type, 0.5)


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Replay safety incident')
    parser.add_argument('--incident', required=True, help='Path to incident JSON')
    parser.add_argument('--with-safeguards', action='store_true',
                       help='Simulate with safeguards')

    args = parser.parse_args()

    replayer = IncidentReplayer()
    incident = replayer.load_incident(args.incident)
    replayer.replay(incident, with_safeguards=args.with_safeguards)


if __name__ == '__main__':
    main()
