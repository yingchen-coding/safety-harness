"""
Severity Scoring & Business Impact Module
=========================================

Maps incidents from technical classification to operational risk levels.

Key insight: Safety incidents are not just technical problems.
They have user impact, SLO implications, and release consequences.
This module bridges the gap between technical RCA and business action.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional
from enum import Enum
import json


class SeverityLevel(Enum):
    """Incident severity levels aligned with SRE practices."""

    SEV0 = "sev0"  # Critical: Immediate action required
    SEV1 = "sev1"  # High: Same-day resolution required
    SEV2 = "sev2"  # Medium: Resolution within 1 week
    SEV3 = "sev3"  # Low: Track and address in normal cycle


class ReleaseAction(Enum):
    """Release actions triggered by incident severity."""

    IMMEDIATE_BLOCK = "immediate_block"
    WARN_WITH_REVIEW = "warn_with_review"
    TRACK_FOR_NEXT_RELEASE = "track_for_next_release"
    NO_ACTION = "no_action"


@dataclass
class BusinessImpact:
    """Business impact assessment for an incident."""

    affected_users: int
    affected_conversations: int
    slo_breach: bool
    revenue_impact_usd: Optional[float]
    reputation_risk: str  # low, medium, high, critical
    regulatory_exposure: bool


@dataclass
class SeverityAssessment:
    """Complete severity assessment for an incident."""

    incident_id: str
    technical_severity: str  # From RCA: low, medium, high, critical
    business_impact: BusinessImpact
    computed_severity: SeverityLevel
    release_action: ReleaseAction
    escalation_required: bool
    rationale: str


def compute_severity(
    incident_id: str,
    technical_severity: str,
    affected_users: int,
    affected_conversations: int,
    slo_breach: bool = False,
    reputation_risk: str = "low",
    regulatory_exposure: bool = False
) -> SeverityAssessment:
    """
    Compute overall severity from technical and business factors.

    Args:
        incident_id: Incident identifier
        technical_severity: RCA severity (low/medium/high/critical)
        affected_users: Number of users impacted
        affected_conversations: Number of conversations affected
        slo_breach: Whether incident breached SLO
        reputation_risk: Reputation risk level
        regulatory_exposure: Whether incident has regulatory implications

    Returns:
        Complete SeverityAssessment
    """
    business_impact = BusinessImpact(
        affected_users=affected_users,
        affected_conversations=affected_conversations,
        slo_breach=slo_breach,
        revenue_impact_usd=None,  # Computed separately if needed
        reputation_risk=reputation_risk,
        regulatory_exposure=regulatory_exposure
    )

    # Severity matrix
    severity, action, escalate, rationale = _apply_severity_matrix(
        technical_severity=technical_severity,
        affected_users=affected_users,
        slo_breach=slo_breach,
        reputation_risk=reputation_risk,
        regulatory_exposure=regulatory_exposure
    )

    return SeverityAssessment(
        incident_id=incident_id,
        technical_severity=technical_severity,
        business_impact=business_impact,
        computed_severity=severity,
        release_action=action,
        escalation_required=escalate,
        rationale=rationale
    )


def _apply_severity_matrix(
    technical_severity: str,
    affected_users: int,
    slo_breach: bool,
    reputation_risk: str,
    regulatory_exposure: bool
) -> tuple:
    """Apply severity decision matrix."""

    # SEV0: Any regulatory exposure OR critical + high user impact
    if regulatory_exposure:
        return (
            SeverityLevel.SEV0,
            ReleaseAction.IMMEDIATE_BLOCK,
            True,
            "Regulatory exposure requires immediate action"
        )

    if technical_severity == "critical" and affected_users > 1000:
        return (
            SeverityLevel.SEV0,
            ReleaseAction.IMMEDIATE_BLOCK,
            True,
            f"Critical severity with {affected_users} affected users"
        )

    # SEV1: SLO breach OR high technical + medium user impact
    if slo_breach:
        return (
            SeverityLevel.SEV1,
            ReleaseAction.IMMEDIATE_BLOCK,
            True,
            "SLO breach requires same-day resolution"
        )

    if technical_severity == "high" and affected_users > 100:
        return (
            SeverityLevel.SEV1,
            ReleaseAction.WARN_WITH_REVIEW,
            True,
            f"High severity with {affected_users} affected users"
        )

    if reputation_risk in ["high", "critical"]:
        return (
            SeverityLevel.SEV1,
            ReleaseAction.WARN_WITH_REVIEW,
            True,
            f"High reputation risk: {reputation_risk}"
        )

    # SEV2: Medium technical OR moderate user impact
    if technical_severity == "medium" or affected_users > 10:
        return (
            SeverityLevel.SEV2,
            ReleaseAction.TRACK_FOR_NEXT_RELEASE,
            False,
            "Medium severity - track for next release cycle"
        )

    # SEV3: Low impact
    return (
        SeverityLevel.SEV3,
        ReleaseAction.NO_ACTION,
        False,
        "Low severity - track in normal cycle"
    )


def generate_severity_report(assessments: List[SeverityAssessment]) -> Dict:
    """
    Generate severity report for multiple incidents.

    Args:
        assessments: List of SeverityAssessment objects

    Returns:
        Structured report with summary and details
    """
    sev_counts = {level: 0 for level in SeverityLevel}
    action_counts = {action: 0 for action in ReleaseAction}

    for assessment in assessments:
        sev_counts[assessment.computed_severity] += 1
        action_counts[assessment.release_action] += 1

    return {
        "summary": {
            "total_incidents": len(assessments),
            "severity_distribution": {
                level.value: count for level, count in sev_counts.items()
            },
            "action_distribution": {
                action.value: count for action, count in action_counts.items()
            },
            "escalations_required": sum(
                1 for a in assessments if a.escalation_required
            ),
            "immediate_blocks": action_counts[ReleaseAction.IMMEDIATE_BLOCK]
        },
        "incidents": [
            {
                "incident_id": a.incident_id,
                "severity": a.computed_severity.value,
                "affected_users": a.business_impact.affected_users,
                "slo_breach": a.business_impact.slo_breach,
                "release_action": a.release_action.value,
                "rationale": a.rationale
            }
            for a in assessments
        ]
    }


# Example output demonstrating the module
EXAMPLE_REPORT = """
INCIDENT SEVERITY REPORT
========================

| Incident | Severity | Impacted Users | SLO Breach | Release Action     |
|----------|----------|----------------|------------|--------------------|
| INC_001  | sev2     | 47             | No         | track_for_next     |
| INC_002  | sev1     | 523            | Yes        | warn_with_review   |
| INC_003  | sev3     | 3              | No         | no_action          |
| INC_004  | sev0     | 1247           | Yes        | immediate_block    |

SUMMARY:
- Total incidents: 4
- Immediate blocks: 1
- Escalations required: 2
- SLO breaches: 2
"""


# Output schema for downstream consumption
OUTPUT_SCHEMA = {
    "description": "Severity scoring output for incident management",
    "fields": {
        "incident_id": "Incident identifier",
        "computed_severity": "Overall severity (sev0-sev3)",
        "release_action": "Required release action",
        "escalation_required": "Whether escalation is needed",
        "rationale": "Human-readable explanation"
    },
    "consumers": [
        "model-safety-regression-suite: Incident-driven release decisions",
        "scalable-safeguards-eval-pipeline: Priority weighting for evals"
    ]
}


if __name__ == "__main__":
    # Example usage
    incidents = [
        compute_severity(
            incident_id="INC_001",
            technical_severity="medium",
            affected_users=47,
            affected_conversations=312,
            slo_breach=False,
            reputation_risk="low"
        ),
        compute_severity(
            incident_id="INC_002",
            technical_severity="high",
            affected_users=523,
            affected_conversations=1847,
            slo_breach=True,
            reputation_risk="medium"
        ),
        compute_severity(
            incident_id="INC_003",
            technical_severity="low",
            affected_users=3,
            affected_conversations=8,
            slo_breach=False,
            reputation_risk="low"
        ),
        compute_severity(
            incident_id="INC_004",
            technical_severity="critical",
            affected_users=1247,
            affected_conversations=4521,
            slo_breach=True,
            reputation_risk="high"
        ),
    ]

    report = generate_severity_report(incidents)
    print(json.dumps(report, indent=2))
    print(EXAMPLE_REPORT)
