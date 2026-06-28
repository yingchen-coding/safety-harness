"""
Adapter for agentic-misuse-benchmark integration.

Allows incident lab to:
1. Check if incident patterns exist in misuse benchmark
2. Generate new benchmark scenarios from incidents
3. Estimate blast radius across benchmark suite
"""

from typing import Optional


class MisuseBenchmarkAdapter:
    """
    Interface to agentic-misuse-benchmark for cross-repo analysis.
    """

    # Simulated benchmark scenario categories
    SCENARIO_CATEGORIES = {
        'prompt_injection': ['injection_basic', 'injection_nested', 'injection_delayed'],
        'policy_erosion': ['erosion_gradual', 'erosion_context', 'erosion_roleplay'],
        'coordinated_misuse': ['coord_decomposition', 'coord_roleplay', 'coord_temporal'],
        'tool_misuse': ['tool_abuse', 'tool_chain', 'tool_hallucination'],
        'intent_drift': ['drift_subtle', 'drift_goal_hijack', 'drift_scope_creep']
    }

    # Simulated scenario counts
    SCENARIO_COUNTS = {
        'prompt_injection': 45,
        'policy_erosion': 38,
        'coordinated_misuse': 52,
        'tool_misuse': 31,
        'intent_drift': 27
    }

    def __init__(self, benchmark_path: Optional[str] = None):
        """
        Initialize adapter.

        Args:
            benchmark_path: Path to benchmark repo (uses simulation if None)
        """
        self.benchmark_path = benchmark_path
        self._connected = benchmark_path is not None

    def find_similar_scenarios(self, failure_type: str, limit: int = 5) -> list[dict]:
        """
        Find benchmark scenarios similar to an incident's failure type.

        Args:
            failure_type: Type of failure from incident
            limit: Max scenarios to return

        Returns:
            List of similar scenario metadata
        """
        categories = self.SCENARIO_CATEGORIES.get(failure_type, [])

        scenarios = []
        for i, cat in enumerate(categories[:limit]):
            scenarios.append({
                'scenario_id': f'{failure_type}_{cat}_{i+1:03d}',
                'category': cat,
                'failure_type': failure_type,
                'similarity_score': 0.85 - (i * 0.05),
                'source': 'agentic-misuse-benchmark'
            })

        return scenarios

    def count_affected_scenarios(self, failure_type: str) -> dict:
        """
        Count how many benchmark scenarios share a vulnerability.

        Args:
            failure_type: Type of failure to check

        Returns:
            Count statistics
        """
        direct_count = self.SCENARIO_COUNTS.get(failure_type, 0)
        total_scenarios = sum(self.SCENARIO_COUNTS.values())

        # Estimate related scenarios (similar failure patterns)
        related_types = self._get_related_types(failure_type)
        related_count = sum(
            self.SCENARIO_COUNTS.get(t, 0) * 0.3
            for t in related_types
        )

        return {
            'direct_matches': direct_count,
            'related_matches': int(related_count),
            'total_scenarios': total_scenarios,
            'affected_percentage': (direct_count + related_count) / total_scenarios
        }

    def generate_benchmark_case(self, incident: dict) -> dict:
        """
        Generate a new benchmark scenario from an incident.

        Args:
            incident: Incident data

        Returns:
            Benchmark scenario specification
        """
        failure_type = incident.get('failure_type', 'unknown')
        incident_id = incident.get('incident_id', 'INC_XXX')

        return {
            'scenario_id': f'postmortem_{incident_id}',
            'category': failure_type,
            'source': 'incident_lab',
            'incident_ref': incident_id,
            'trajectory_template': self._extract_trajectory_template(incident),
            'expected_detection': {
                'should_detect': True,
                'detection_turn': incident.get('first_unsafe_turn', -1) - 1,
                'severity': incident.get('severity', 'high')
            },
            'tags': ['postmortem', 'regression', failure_type]
        }

    def _get_related_types(self, failure_type: str) -> list[str]:
        """Get failure types related to the given type."""
        relations = {
            'prompt_injection': ['tool_misuse'],
            'policy_erosion': ['intent_drift', 'coordinated_misuse'],
            'coordinated_misuse': ['policy_erosion', 'intent_drift'],
            'tool_misuse': ['prompt_injection'],
            'intent_drift': ['policy_erosion']
        }
        return relations.get(failure_type, [])

    def _extract_trajectory_template(self, incident: dict) -> dict:
        """Extract trajectory template from incident."""
        conversation = incident.get('conversation', [])
        if not conversation:
            sessions = incident.get('sessions', [])
            if sessions:
                conversation = sessions[0].get('conversation', [])

        return {
            'num_turns': len(conversation),
            'failure_turn': incident.get('first_unsafe_turn', -1),
            'pattern': incident.get('failure_type', 'unknown')
        }
