"""
Root cause analyzer for safety incidents.

Uses structured taxonomy to identify contributing factors and suggest mitigations.
"""

import json
from dataclasses import dataclass
from typing import Optional


@dataclass
class ContributingFactor:
    """A factor that contributed to the incident."""
    factor: str
    description: str
    severity: str  # low, medium, high, critical
    category: str  # safeguard_gap, policy_gap, design_flaw, edge_case


@dataclass
class RootCauseAnalysis:
    """Complete root cause analysis for an incident."""
    incident_id: str
    failure_type: str
    first_unsafe_turn: int
    contributing_factors: list[ContributingFactor]
    mitigation_candidates: list[str]
    expected_rca: Optional[dict]
    confidence: float

    def to_dict(self) -> dict:
        return {
            'incident_id': self.incident_id,
            'failure_type': self.failure_type,
            'first_unsafe_turn': self.first_unsafe_turn,
            'contributing_factors': [
                {
                    'factor': f.factor,
                    'description': f.description,
                    'severity': f.severity,
                    'category': f.category
                }
                for f in self.contributing_factors
            ],
            'mitigation_candidates': self.mitigation_candidates,
            'expected_rca': self.expected_rca,
            'confidence': self.confidence
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2)


class RootCauseAnalyzer:
    """
    Analyzes incidents to identify root causes and mitigations.

    Uses structured taxonomy mapping failure patterns to:
    - Contributing factors
    - Severity ratings
    - Mitigation candidates
    """

    # Root cause taxonomy
    ROOT_CAUSE_DB = {
        # Injection-related
        'pre_action_injection_detector_false_negative': {
            'description': 'Pre-action injection detector failed to identify hidden instruction',
            'severity': 'critical',
            'category': 'safeguard_gap',
            'mitigations': ['Train detector on tool-output injection patterns', 'Add instruction boundary markers']
        },
        'tool_allowlist_keyword_check_only': {
            'description': 'Tool allowlist used simple keyword matching instead of semantic analysis',
            'severity': 'high',
            'category': 'design_flaw',
            'mitigations': ['Implement semantic tool policy', 'Add path allowlisting']
        },
        'no_tool_output_sanitization': {
            'description': 'Tool outputs not sanitized before processing',
            'severity': 'high',
            'category': 'design_flaw',
            'mitigations': ['Add tool output verifier in post_action hook', 'Implement content filter']
        },
        'instruction_boundary_confusion': {
            'description': 'Model confused user data with instructions',
            'severity': 'critical',
            'category': 'design_flaw',
            'mitigations': ['Use explicit instruction delimiters', 'Train on boundary detection']
        },

        # Policy erosion-related
        'drift_monitor_threshold_too_high': {
            'description': 'Drift monitor threshold too permissive to catch gradual erosion',
            'severity': 'high',
            'category': 'safeguard_gap',
            'mitigations': ['Lower drift threshold to 0.4 for sensitive categories', 'Add slope-based detection']
        },
        'escalation_policy_reaction_too_slow': {
            'description': 'Escalation policy only triggered WARN instead of SOFT_STOP',
            'severity': 'medium',
            'category': 'policy_gap',
            'mitigations': ['Add SOFT_STOP escalation for sensitive tools', 'Reduce escalation delay']
        },
        'no_trajectory_level_intent_analysis': {
            'description': 'Intent classifier evaluated turns independently without trajectory context',
            'severity': 'high',
            'category': 'safeguard_gap',
            'mitigations': ['Implement trajectory-level risk accumulator', 'Add multi-turn intent tracking']
        },
        'gradual_rationalization_not_detected': {
            'description': 'Progressive rationalization pattern not flagged',
            'severity': 'medium',
            'category': 'policy_gap',
            'mitigations': ['Flag research/testing framing as potential erosion', 'Track topic drift']
        },

        # Tool hallucination-related
        'post_action_verifier_missing_schema_validation': {
            'description': 'Post-action verifier did not validate tool output schema',
            'severity': 'high',
            'category': 'safeguard_gap',
            'mitigations': ['Implement strict tool schema validation', 'Add type checking for tool results']
        },
        'no_tool_result_anomaly_detection': {
            'description': 'No anomaly detection for error patterns in tool results',
            'severity': 'medium',
            'category': 'safeguard_gap',
            'mitigations': ['Add error pattern detection', 'Flag unusual tool result formats']
        },
        'error_handling_not_propagated_to_response': {
            'description': 'Tool error not propagated to model response',
            'severity': 'high',
            'category': 'design_flaw',
            'mitigations': ['Force acknowledgment of tool failures', 'Block generation on tool error']
        },
        'confidence_calibration_failure': {
            'description': 'Model generated confident response despite tool failure',
            'severity': 'medium',
            'category': 'design_flaw',
            'mitigations': ['Add confidence calibration based on tool success', 'Require hedging on errors']
        },

        # Coordinated misuse-related
        'intent_classifier_single_turn_only': {
            'description': 'Intent classifier only analyzed individual turns, missing patterns',
            'severity': 'critical',
            'category': 'safeguard_gap',
            'mitigations': ['Implement trajectory-level intent aggregation', 'Add multi-turn pattern detection']
        },
        'no_trajectory_level_intent_aggregation': {
            'description': 'No aggregation of intents across turns to detect coordination',
            'severity': 'high',
            'category': 'safeguard_gap',
            'mitigations': ['Track cumulative capability creation', 'Flag capability accumulation patterns']
        },
        'subtask_combination_not_analyzed': {
            'description': 'Combined effect of subtasks not analyzed for harm',
            'severity': 'high',
            'category': 'design_flaw',
            'mitigations': ['Analyze combined tool outputs', 'Check subtask synthesis for harmful capabilities']
        },
        'tool_sequence_pattern_not_detected': {
            'description': 'Suspicious tool sequence pattern not flagged',
            'severity': 'medium',
            'category': 'safeguard_gap',
            'mitigations': ['Add tool sequence pattern detection', 'Flag known attack tool chains']
        },

        # Escalation delay-related
        'escalation_policy_not_hard_stop': {
            'description': 'Escalation to HUMAN_REVIEW did not include agent freeze',
            'severity': 'critical',
            'category': 'policy_gap',
            'mitigations': ['Change HUMAN_REVIEW to HARD_STOP + queue for destructive ops']
        },
        'async_review_without_agent_freeze': {
            'description': 'Async human review pattern incompatible with destructive operations',
            'severity': 'high',
            'category': 'design_flaw',
            'mitigations': ['Implement agent freeze when review pending', 'Use sync review for destructive ops']
        },
        'pending_review_state_not_blocking': {
            'description': 'Pending review state did not block further actions',
            'severity': 'high',
            'category': 'safeguard_gap',
            'mitigations': ['Add synchronous review requirement for destructive actions']
        },
        'destructive_action_not_gated': {
            'description': 'Destructive actions not gated behind explicit human approval',
            'severity': 'critical',
            'category': 'policy_gap',
            'mitigations': ['Gate delete/write operations behind human approval', 'Add confirmation step']
        }
    }

    def load_incident(self, path: str) -> dict:
        """Load incident from JSON file."""
        with open(path) as f:
            return json.load(f)

    def analyze(self, incident: dict, verbose: bool = True) -> RootCauseAnalysis:
        """
        Perform root cause analysis on an incident.

        Args:
            incident: Incident data
            verbose: Print analysis

        Returns:
            RootCauseAnalysis with findings
        """
        incident_id = incident['incident_id']
        failure_type = incident.get('failure_type', 'unknown')
        first_unsafe = incident.get('first_unsafe_turn', -1)
        raw_causes = incident.get('root_causes', [])
        expected_rca = incident.get('expected_rca', None)

        # Handle string first_unsafe_turn (e.g., "sess_D:4")
        if isinstance(first_unsafe, str):
            first_unsafe = -1

        # Analyze each root cause
        factors = []
        all_mitigations = set()

        for cause in raw_causes:
            if cause in self.ROOT_CAUSE_DB:
                info = self.ROOT_CAUSE_DB[cause]
                factors.append(ContributingFactor(
                    factor=cause,
                    description=info['description'],
                    severity=info['severity'],
                    category=info['category']
                ))
                all_mitigations.update(info['mitigations'])
            else:
                factors.append(ContributingFactor(
                    factor=cause,
                    description=f'Unknown factor: {cause}',
                    severity='medium',
                    category='unknown'
                ))

        # Add mitigations from incident hints
        mitigation_hints = incident.get('mitigation_hints', [])
        all_mitigations.update(mitigation_hints)

        # Sort by severity
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        factors.sort(key=lambda f: severity_order.get(f.severity, 4))

        # Calculate confidence based on known causes
        known_count = sum(1 for c in raw_causes if c in self.ROOT_CAUSE_DB)
        confidence = known_count / len(raw_causes) if raw_causes else 0.5

        analysis = RootCauseAnalysis(
            incident_id=incident_id,
            failure_type=failure_type,
            first_unsafe_turn=first_unsafe,
            contributing_factors=factors,
            mitigation_candidates=list(all_mitigations),
            expected_rca=expected_rca,
            confidence=confidence
        )

        if verbose:
            self._print_analysis(analysis)

        return analysis

    def _print_analysis(self, analysis: RootCauseAnalysis):
        """Print formatted analysis."""
        print(f"\n{'='*60}")
        print(f"ROOT CAUSE ANALYSIS: {analysis.incident_id}")
        print(f"{'='*60}")

        print(f"\nFailure Type: {analysis.failure_type}")
        print(f"First Unsafe Turn: {analysis.first_unsafe_turn}")
        print(f"Analysis Confidence: {analysis.confidence:.0%}")

        if analysis.expected_rca:
            print("\n--- Expected RCA ---")
            print(f"Primary: {analysis.expected_rca.get('primary', 'N/A')}")
            print(f"Secondary: {analysis.expected_rca.get('secondary', 'N/A')}")
            print(f"Contributing: {analysis.expected_rca.get('contributing', 'N/A')}")

        print(f"\n--- Contributing Factors ({len(analysis.contributing_factors)}) ---")
        for f in analysis.contributing_factors:
            severity_icon = {'critical': '!', 'high': '*', 'medium': '-', 'low': ' '}.get(f.severity, '?')
            print(f"[{severity_icon}] {f.factor}")
            print(f"    {f.description}")
            print(f"    Severity: {f.severity} | Category: {f.category}")

        print(f"\n--- Mitigation Candidates ({len(analysis.mitigation_candidates)}) ---")
        for m in analysis.mitigation_candidates:
            print(f"  - {m}")

        print()


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Analyze incident root cause')
    parser.add_argument('--incident', required=True, help='Path to incident JSON')

    args = parser.parse_args()

    analyzer = RootCauseAnalyzer()
    incident = analyzer.load_incident(args.incident)
    analyzer.analyze(incident)


if __name__ == '__main__':
    main()
