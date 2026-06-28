"""
Failure taxonomy with weighted scoring for root cause analysis.

Provides enum-based failure types and risk scoring for production use.
"""

from enum import Enum
from dataclasses import dataclass
from typing import List, Dict, Optional


class FailureType(str, Enum):
    """Taxonomy of failure modes in agentic safety incidents."""

    # Detection failures
    PRE_ACTION_DETECTION_FN = "pre_action_detection_fn"
    TRAJECTORY_MONITORING_FN = "trajectory_monitoring_fn"
    TOOL_VERIFICATION_FN = "tool_verification_fn"

    # Policy failures
    ESCALATION_POLICY_FN = "escalation_policy_fn"
    HUMAN_REVIEW_PROTOCOL_FN = "human_review_protocol_fn"
    POLICY_SCHEMA_MISMATCH = "policy_schema_mismatch"

    # Analysis failures
    INTENT_AGGREGATION_FN = "intent_aggregation_fn"
    THRESHOLD_MISCONFIG = "threshold_misconfig"

    # Tool failures
    TOOL_HALLUCINATION = "tool_hallucination"
    TOOL_CHAIN_ABUSE = "tool_chain_abuse"

    # Coordination failures
    CROSS_SESSION_BLIND = "cross_session_blind"
    CAPABILITY_ACCUMULATION = "capability_accumulation"


# Severity weights for risk scoring
FAILURE_WEIGHTS: Dict[FailureType, float] = {
    # Detection failures (moderate weight - can be caught downstream)
    FailureType.PRE_ACTION_DETECTION_FN: 1.2,
    FailureType.TRAJECTORY_MONITORING_FN: 1.5,
    FailureType.TOOL_VERIFICATION_FN: 1.3,

    # Policy failures (high weight - fundamental gaps)
    FailureType.ESCALATION_POLICY_FN: 1.6,
    FailureType.HUMAN_REVIEW_PROTOCOL_FN: 1.8,  # Highest - creates false confidence
    FailureType.POLICY_SCHEMA_MISMATCH: 1.1,

    # Analysis failures (moderate weight)
    FailureType.INTENT_AGGREGATION_FN: 1.4,
    FailureType.THRESHOLD_MISCONFIG: 1.0,

    # Tool failures (moderate-high weight)
    FailureType.TOOL_HALLUCINATION: 1.4,
    FailureType.TOOL_CHAIN_ABUSE: 1.3,

    # Coordination failures (high weight - hard to detect)
    FailureType.CROSS_SESSION_BLIND: 1.7,
    FailureType.CAPABILITY_ACCUMULATION: 1.5,
}


# Mapping from incident failure_type to taxonomy entries
FAILURE_TYPE_MAPPING: Dict[str, List[FailureType]] = {
    'prompt_injection': [
        FailureType.PRE_ACTION_DETECTION_FN,
        FailureType.TOOL_VERIFICATION_FN
    ],
    'policy_erosion': [
        FailureType.TRAJECTORY_MONITORING_FN,
        FailureType.THRESHOLD_MISCONFIG,
        FailureType.ESCALATION_POLICY_FN
    ],
    'tool_hallucination': [
        FailureType.TOOL_HALLUCINATION,
        FailureType.TOOL_VERIFICATION_FN
    ],
    'coordinated_misuse': [
        FailureType.INTENT_AGGREGATION_FN,
        FailureType.CAPABILITY_ACCUMULATION
    ],
    'escalation_delay': [
        FailureType.HUMAN_REVIEW_PROTOCOL_FN,
        FailureType.ESCALATION_POLICY_FN
    ],
    'cross_session': [
        FailureType.CROSS_SESSION_BLIND,
        FailureType.INTENT_AGGREGATION_FN
    ]
}


@dataclass
class RootCauseEntry:
    """A single root cause with evidence and confidence."""
    failure_type: FailureType
    evidence_turns: List[int]
    confidence: float  # 0.0 - 1.0
    description: Optional[str] = None


def score_root_causes(root_causes: List[RootCauseEntry]) -> float:
    """
    Aggregate weighted risk score from root causes.

    Higher score = more severe systemic weakness.
    Score interpretation:
    - < 1.0: Low risk, localized issue
    - 1.0 - 2.0: Moderate risk, should address
    - 2.0 - 3.0: High risk, prioritize fix
    - > 3.0: Critical risk, block release
    """
    score = 0.0
    for rc in root_causes:
        weight = FAILURE_WEIGHTS.get(rc.failure_type, 1.0)
        score += weight * rc.confidence
    return round(score, 3)


def summarize_root_causes(root_causes: List[RootCauseEntry]) -> Dict[str, float]:
    """Aggregate confidence by failure type."""
    summary: Dict[str, float] = {}
    for rc in root_causes:
        key = rc.failure_type.value
        summary[key] = summary.get(key, 0.0) + rc.confidence
    return summary


def map_incident_to_taxonomy(incident_failure_type: str) -> List[FailureType]:
    """Map incident failure type to taxonomy entries."""
    return FAILURE_TYPE_MAPPING.get(incident_failure_type, [])


def get_failure_weight(failure_type: FailureType) -> float:
    """Get severity weight for a failure type."""
    return FAILURE_WEIGHTS.get(failure_type, 1.0)


def categorize_by_severity(root_causes: List[RootCauseEntry]) -> Dict[str, List[RootCauseEntry]]:
    """Categorize root causes by severity level."""
    categories = {
        'critical': [],  # weight >= 1.7
        'high': [],      # weight >= 1.4
        'medium': [],    # weight >= 1.1
        'low': []        # weight < 1.1
    }

    for rc in root_causes:
        weight = get_failure_weight(rc.failure_type)
        if weight >= 1.7:
            categories['critical'].append(rc)
        elif weight >= 1.4:
            categories['high'].append(rc)
        elif weight >= 1.1:
            categories['medium'].append(rc)
        else:
            categories['low'].append(rc)

    return categories
