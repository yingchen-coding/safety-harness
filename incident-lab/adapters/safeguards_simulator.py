"""
Adapter for agentic-safeguards-simulator integration.

Allows incident lab to:
1. Simulate incidents with safeguards enabled
2. Identify which safeguard hooks would have caught the failure
3. Estimate prevention probability
"""

from typing import Optional


class SafeguardsSimulatorAdapter:
    """
    Interface to agentic-safeguards-simulator for counterfactual analysis.
    """

    # Safeguard hooks and their detection capabilities
    SAFEGUARD_HOOKS = {
        'pre_action': {
            'detects': ['prompt_injection', 'tool_misuse'],
            'checks': ['injection_patterns', 'tool_allowlist', 'input_sanitization'],
            'latency_ms': 15
        },
        'mid_trajectory': {
            'detects': ['policy_erosion', 'intent_drift'],
            'checks': ['drift_monitor', 'intent_tracker', 'risk_accumulator'],
            'latency_ms': 25
        },
        'post_action': {
            'detects': ['tool_misuse', 'data_exfiltration'],
            'checks': ['output_validator', 'schema_verifier', 'anomaly_detector'],
            'latency_ms': 20
        },
        'cross_session': {
            'detects': ['coordinated_misuse'],
            'checks': ['pattern_analyzer', 'entity_tracker', 'temporal_correlation'],
            'latency_ms': 50
        }
    }

    # Escalation levels
    ESCALATION_LEVELS = [
        'NONE',
        'CLARIFY',
        'WARN',
        'SOFT_STOP',
        'HARD_STOP',
        'HUMAN_REVIEW'
    ]

    def __init__(self, simulator_path: Optional[str] = None):
        """
        Initialize adapter.

        Args:
            simulator_path: Path to safeguards-simulator repo
        """
        self.simulator_path = simulator_path
        self._connected = simulator_path is not None

    def identify_relevant_hooks(self, failure_type: str) -> list[dict]:
        """
        Identify which safeguard hooks are relevant to a failure type.

        Args:
            failure_type: Type of failure from incident

        Returns:
            List of relevant hooks with detection info
        """
        relevant = []

        for hook_name, hook_info in self.SAFEGUARD_HOOKS.items():
            if failure_type in hook_info['detects']:
                relevant.append({
                    'hook': hook_name,
                    'checks': hook_info['checks'],
                    'relevance': 'primary' if hook_info['detects'][0] == failure_type else 'secondary',
                    'latency_ms': hook_info['latency_ms']
                })

        return relevant

    def simulate_counterfactual(self, incident: dict) -> dict:
        """
        Simulate what would have happened with safeguards enabled.

        Args:
            incident: Incident data

        Returns:
            Counterfactual analysis
        """
        failure_type = incident.get('failure_type', 'unknown')
        first_unsafe = incident.get('first_unsafe_turn', -1)
        severity = incident.get('severity', 'high')

        relevant_hooks = self.identify_relevant_hooks(failure_type)

        if not relevant_hooks:
            return {
                'would_prevent': False,
                'reason': 'no_applicable_safeguard',
                'recommendation': 'new_safeguard_needed'
            }

        primary_hook = next((h for h in relevant_hooks if h['relevance'] == 'primary'), relevant_hooks[0])

        # Estimate detection turn
        detection_turn = max(1, first_unsafe - 1) if isinstance(first_unsafe, int) else 'unknown'

        # Estimate escalation level
        escalation = self._estimate_escalation(failure_type, severity)

        # Calculate prevention probability
        prevention_prob = self._calculate_prevention_probability(failure_type, primary_hook)

        return {
            'would_prevent': prevention_prob > 0.7,
            'prevention_probability': prevention_prob,
            'detection_hook': primary_hook['hook'],
            'detection_checks': primary_hook['checks'],
            'estimated_detection_turn': detection_turn,
            'escalation_action': escalation,
            'all_relevant_hooks': [h['hook'] for h in relevant_hooks]
        }

    def identify_safeguard_gaps(self, incident: dict) -> list[dict]:
        """
        Identify gaps in safeguard coverage for an incident.

        Args:
            incident: Incident data

        Returns:
            List of identified gaps
        """
        failure_type = incident.get('failure_type', 'unknown')
        root_causes = incident.get('root_causes', [])

        gaps = []

        # Check for hook coverage gaps
        relevant_hooks = self.identify_relevant_hooks(failure_type)
        if not relevant_hooks:
            gaps.append({
                'gap_type': 'missing_hook',
                'description': f'No hook designed for {failure_type}',
                'severity': 'high',
                'recommendation': f'Add {failure_type}_detector to pre_action or mid_trajectory'
            })

        # Analyze root causes for specific gaps
        for cause in root_causes:
            if 'threshold' in cause.lower():
                gaps.append({
                    'gap_type': 'threshold_misconfiguration',
                    'description': 'Detection threshold too permissive',
                    'severity': 'medium',
                    'recommendation': 'Lower drift/risk thresholds'
                })
            elif 'false_negative' in cause.lower() or 'fn' in cause.lower():
                gaps.append({
                    'gap_type': 'classifier_weakness',
                    'description': 'Classifier missed this pattern',
                    'severity': 'high',
                    'recommendation': 'Add incident pattern to training data'
                })
            elif 'escalation' in cause.lower():
                gaps.append({
                    'gap_type': 'escalation_delay',
                    'description': 'Escalation policy too slow',
                    'severity': 'medium',
                    'recommendation': 'Reduce escalation delay, consider hard stop'
                })

        return gaps

    def _estimate_escalation(self, failure_type: str, severity: str) -> str:
        """Estimate appropriate escalation level."""
        if severity == 'critical':
            return 'HARD_STOP'
        elif failure_type in ['prompt_injection', 'coordinated_misuse']:
            return 'HARD_STOP'
        elif failure_type in ['policy_erosion', 'intent_drift']:
            return 'SOFT_STOP'
        else:
            return 'WARN'

    def _calculate_prevention_probability(self, failure_type: str, hook: dict) -> float:
        """Calculate probability of prevention with given hook."""
        base_rates = {
            'prompt_injection': 0.92,
            'policy_erosion': 0.78,
            'tool_misuse': 0.85,
            'intent_drift': 0.72,
            'coordinated_misuse': 0.55
        }

        base = base_rates.get(failure_type, 0.5)

        # Adjust for hook type
        if hook['relevance'] == 'primary':
            return min(0.98, base * 1.1)
        else:
            return base * 0.9
