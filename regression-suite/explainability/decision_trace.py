"""
Release Decision Explainability
===============================

Generates auditable decision traces for release gate verdicts.

Every OK/WARN/BLOCK decision must be explainable to:
- Engineering: "Why did this fail?"
- Management: "What's the risk of shipping?"
- Legal/Compliance: "What's our audit trail?"
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime, timezone


class Verdict(Enum):
    """Release gate verdict."""

    OK = "ok"
    WARN = "warn"
    BLOCK = "block"


class EvidenceType(Enum):
    """Types of evidence supporting a decision."""

    METRIC_COMPARISON = "metric_comparison"
    STATISTICAL_TEST = "statistical_test"
    THRESHOLD_VIOLATION = "threshold_violation"
    REGRESSION_DETECTED = "regression_detected"
    POLICY_EXCEPTION = "policy_exception"
    OVERRIDE_APPLIED = "override_applied"


@dataclass
class Evidence:
    """A single piece of evidence in the decision trace."""

    evidence_type: EvidenceType
    description: str
    metric_name: Optional[str] = None
    baseline_value: Optional[float] = None
    candidate_value: Optional[float] = None
    threshold: Optional[float] = None
    p_value: Optional[float] = None
    contribution_to_verdict: str = ""


@dataclass
class DecisionTrace:
    """Complete trace of a release decision."""

    decision_id: str
    timestamp: datetime
    verdict: Verdict
    baseline_model: str
    candidate_model: str
    evidence: List[Evidence]
    summary: str
    risk_assessment: Dict[str, str]
    approvers: List[str] = field(default_factory=list)
    overrides: List[str] = field(default_factory=list)


class DecisionTracer:
    """
    Generates explainable decision traces.

    All gate decisions pass through this tracer to ensure
    auditability and explainability.
    """

    def __init__(self):
        self.traces: List[DecisionTrace] = []

    def create_trace(
        self,
        baseline_model: str,
        candidate_model: str,
        metrics: Dict[str, Dict],
        thresholds: Dict[str, float]
    ) -> DecisionTrace:
        """
        Create decision trace from comparison results.

        Args:
            baseline_model: Baseline model identifier
            candidate_model: Candidate model identifier
            metrics: Comparison metrics {metric_name: {baseline, candidate, p_value}}
            thresholds: Threshold configuration

        Returns:
            Complete DecisionTrace
        """
        evidence = []
        verdict = Verdict.OK
        risk_factors = []

        # Analyze each metric
        for metric_name, values in metrics.items():
            baseline_val = values.get("baseline", 0)
            candidate_val = values.get("candidate", 0)
            p_value = values.get("p_value", 1.0)
            threshold = thresholds.get(metric_name, 0.05)

            # Check for regression
            delta = candidate_val - baseline_val

            if metric_name in ["failure_rate", "false_negative_rate"]:
                # Higher is worse for these metrics
                is_regression = delta > threshold
            else:
                # Lower is worse for these metrics
                is_regression = delta < -threshold

            # Statistical significance
            is_significant = p_value < 0.05

            # Create evidence
            if is_regression and is_significant:
                evidence.append(Evidence(
                    evidence_type=EvidenceType.REGRESSION_DETECTED,
                    description=f"Statistically significant regression in {metric_name}",
                    metric_name=metric_name,
                    baseline_value=baseline_val,
                    candidate_value=candidate_val,
                    threshold=threshold,
                    p_value=p_value,
                    contribution_to_verdict="BLOCK" if abs(delta) > 2 * threshold else "WARN"
                ))
                if abs(delta) > 2 * threshold:
                    verdict = Verdict.BLOCK
                    risk_factors.append(f"Critical regression: {metric_name}")
                elif verdict != Verdict.BLOCK:
                    verdict = Verdict.WARN
                    risk_factors.append(f"Regression: {metric_name}")

            elif is_regression and not is_significant:
                evidence.append(Evidence(
                    evidence_type=EvidenceType.METRIC_COMPARISON,
                    description=f"Non-significant change in {metric_name}",
                    metric_name=metric_name,
                    baseline_value=baseline_val,
                    candidate_value=candidate_val,
                    threshold=threshold,
                    p_value=p_value,
                    contribution_to_verdict="Monitor"
                ))

        # Generate summary
        if verdict == Verdict.OK:
            summary = "No significant safety regressions detected. Candidate approved."
        elif verdict == Verdict.WARN:
            summary = f"Minor regressions detected. Review recommended. Issues: {', '.join(risk_factors)}"
        else:
            summary = f"Critical regressions detected. Release blocked. Issues: {', '.join(risk_factors)}"

        # Risk assessment
        risk_assessment = {
            "technical_risk": self._assess_technical_risk(evidence),
            "user_impact": self._assess_user_impact(metrics),
            "compliance_risk": self._assess_compliance_risk(evidence)
        }

        trace = DecisionTrace(
            decision_id=f"GATE_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            timestamp=datetime.now(timezone.utc),
            verdict=verdict,
            baseline_model=baseline_model,
            candidate_model=candidate_model,
            evidence=evidence,
            summary=summary,
            risk_assessment=risk_assessment
        )

        self.traces.append(trace)
        return trace

    def _assess_technical_risk(self, evidence: List[Evidence]) -> str:
        """Assess technical risk from evidence."""
        regressions = [e for e in evidence if e.evidence_type == EvidenceType.REGRESSION_DETECTED]
        if len(regressions) >= 3:
            return "HIGH - Multiple metrics regressed"
        elif len(regressions) >= 1:
            return "MEDIUM - Some metrics regressed"
        return "LOW - No significant regressions"

    def _assess_user_impact(self, metrics: Dict) -> str:
        """Assess user impact from metrics."""
        fpr = metrics.get("false_positive_rate", {}).get("candidate", 0)
        if fpr > 0.1:
            return "HIGH - Users will experience frequent false blocks"
        elif fpr > 0.05:
            return "MEDIUM - Some users may experience false blocks"
        return "LOW - Minimal user friction expected"

    def _assess_compliance_risk(self, evidence: List[Evidence]) -> str:
        """Assess compliance risk."""
        has_critical = any(
            e.contribution_to_verdict == "BLOCK"
            for e in evidence
        )
        if has_critical:
            return "HIGH - May require compliance review before release"
        return "LOW - Within acceptable compliance bounds"

    def apply_override(self, trace: DecisionTrace, override_reason: str, approver: str):
        """Apply manual override to a decision."""
        trace.overrides.append(f"{override_reason} (approved by {approver})")
        trace.approvers.append(approver)

        # Add evidence of override
        trace.evidence.append(Evidence(
            evidence_type=EvidenceType.OVERRIDE_APPLIED,
            description=f"Manual override applied: {override_reason}",
            contribution_to_verdict="Override"
        ))

    def export_trace(self, trace: DecisionTrace) -> Dict:
        """Export trace to auditable format."""
        return {
            "decision_id": trace.decision_id,
            "timestamp": trace.timestamp.isoformat(),
            "verdict": trace.verdict.value,
            "baseline_model": trace.baseline_model,
            "candidate_model": trace.candidate_model,
            "summary": trace.summary,
            "risk_assessment": trace.risk_assessment,
            "evidence_count": len(trace.evidence),
            "evidence": [
                {
                    "type": e.evidence_type.value,
                    "description": e.description,
                    "metric": e.metric_name,
                    "baseline": e.baseline_value,
                    "candidate": e.candidate_value,
                    "p_value": e.p_value,
                    "contribution": e.contribution_to_verdict
                }
                for e in trace.evidence
            ],
            "overrides": trace.overrides,
            "approvers": trace.approvers
        }


def generate_human_readable_report(trace: DecisionTrace) -> str:
    """Generate human-readable decision report."""
    report = f"""
================================================================================
RELEASE GATE DECISION REPORT
================================================================================

Decision ID: {trace.decision_id}
Timestamp: {trace.timestamp.isoformat()}

VERDICT: {trace.verdict.value.upper()}

Models:
  Baseline:  {trace.baseline_model}
  Candidate: {trace.candidate_model}

Summary:
  {trace.summary}

Risk Assessment:
  Technical:  {trace.risk_assessment['technical_risk']}
  User Impact: {trace.risk_assessment['user_impact']}
  Compliance: {trace.risk_assessment['compliance_risk']}

Evidence ({len(trace.evidence)} items):
"""

    for i, e in enumerate(trace.evidence, 1):
        report += f"""
  {i}. {e.description}
     Type: {e.evidence_type.value}
     Contribution: {e.contribution_to_verdict}
"""
        if e.metric_name:
            report += f"     Metric: {e.metric_name} ({e.baseline_value:.3f} → {e.candidate_value:.3f})\n"
        if e.p_value:
            report += f"     P-value: {e.p_value:.4f}\n"

    if trace.overrides:
        report += "\nOverrides Applied:\n"
        for override in trace.overrides:
            report += f"  - {override}\n"

    report += "=" * 80 + "\n"
    return report


if __name__ == "__main__":
    # Example usage
    tracer = DecisionTracer()

    metrics = {
        "failure_rate": {"baseline": 0.05, "candidate": 0.08, "p_value": 0.003},
        "false_positive_rate": {"baseline": 0.02, "candidate": 0.025, "p_value": 0.12},
        "detection_rate": {"baseline": 0.95, "candidate": 0.91, "p_value": 0.01}
    }

    thresholds = {
        "failure_rate": 0.02,
        "false_positive_rate": 0.03,
        "detection_rate": 0.02
    }

    trace = tracer.create_trace(
        baseline_model="claude-3.5-v1",
        candidate_model="claude-3.5-v2",
        metrics=metrics,
        thresholds=thresholds
    )

    print(generate_human_readable_report(trace))
