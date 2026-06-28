"""
Human-in-the-Loop Review Interface

Production safety systems require human oversight for high-stakes decisions.
This module implements a review workflow that:

1. Identifies decisions requiring human review
2. Routes reviews to appropriate reviewers based on risk tier
3. Enforces review SLAs and escalation
4. Maintains audit trail of all review decisions

Design Philosophy:
- Automated systems propose, humans dispose (for high-risk decisions)
- Review requirements scale with risk severity
- No human review = no override of BLOCK verdicts
- All reviews are logged immutably
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional
import json
import hashlib


class ReviewTier(Enum):
    """Risk-based review tiers with escalating requirements."""

    TIER_1 = "tier_1"  # Single reviewer (Safety Engineer)
    TIER_2 = "tier_2"  # Two reviewers (Safety Engineer + Safety Lead)
    TIER_3 = "tier_3"  # Committee review (Safety Lead + Legal + Executive)
    EMERGENCY = "emergency"  # Expedited review with post-hoc justification


class ReviewStatus(Enum):
    """Review lifecycle states."""

    PENDING = "pending"
    IN_REVIEW = "in_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"
    EXPIRED = "expired"
    WITHDRAWN = "withdrawn"


@dataclass
class ReviewRequirement:
    """Conditions that trigger human review."""

    condition: str  # e.g., "verdict == BLOCK"
    tier: ReviewTier
    sla_hours: int  # Max time to complete review
    escalation_path: list[str]  # Roles to escalate to if SLA breached
    justification_required: bool = True

    # Risk categories that require this review level
    risk_categories: list[str] = field(default_factory=list)

    @staticmethod
    def default_requirements() -> list["ReviewRequirement"]:
        """Default review requirements for production deployment."""
        return [
            ReviewRequirement(
                condition="verdict == BLOCK AND override_requested",
                tier=ReviewTier.TIER_3,
                sla_hours=24,
                escalation_path=["Safety Lead", "VP Engineering", "CEO"],
                risk_categories=["coordinated_misuse", "injection", "capability_accumulation"],
            ),
            ReviewRequirement(
                condition="verdict == WARN AND business_risk == CRITICAL",
                tier=ReviewTier.TIER_2,
                sla_hours=12,
                escalation_path=["Safety Lead", "VP Engineering"],
                risk_categories=["policy_erosion", "tool_misuse"],
            ),
            ReviewRequirement(
                condition="statistical_power < 0.80",
                tier=ReviewTier.TIER_1,
                sla_hours=8,
                escalation_path=["Safety Lead"],
                risk_categories=[],
            ),
            ReviewRequirement(
                condition="new_failure_mode_detected",
                tier=ReviewTier.TIER_2,
                sla_hours=24,
                escalation_path=["Safety Lead", "Research Lead"],
                risk_categories=[],
            ),
        ]


@dataclass
class HumanReviewRequest:
    """A request for human review of a release decision."""

    request_id: str
    created_at: datetime

    # What is being reviewed
    release_id: str
    model_version: str
    automated_verdict: str  # OK, WARN, BLOCK
    requested_action: str  # "proceed", "override", "investigate"

    # Risk context
    risk_tier: ReviewTier
    risk_categories: list[str]
    regression_summary: dict

    # Evidence package
    evidence_hash: str  # SHA256 of evidence package
    evidence_artifacts: list[str]  # Paths to supporting artifacts

    # Review metadata
    requestor: str
    requestor_justification: str
    sla_deadline: datetime
    status: ReviewStatus = ReviewStatus.PENDING

    # Escalation tracking
    escalation_count: int = 0
    current_assignees: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize for storage and API."""
        return {
            "request_id": self.request_id,
            "created_at": self.created_at.isoformat(),
            "release_id": self.release_id,
            "model_version": self.model_version,
            "automated_verdict": self.automated_verdict,
            "requested_action": self.requested_action,
            "risk_tier": self.risk_tier.value,
            "risk_categories": self.risk_categories,
            "regression_summary": self.regression_summary,
            "evidence_hash": self.evidence_hash,
            "evidence_artifacts": self.evidence_artifacts,
            "requestor": self.requestor,
            "requestor_justification": self.requestor_justification,
            "sla_deadline": self.sla_deadline.isoformat(),
            "status": self.status.value,
            "escalation_count": self.escalation_count,
            "current_assignees": self.current_assignees,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HumanReviewRequest":
        """Deserialize from storage."""
        return cls(
            request_id=data["request_id"],
            created_at=datetime.fromisoformat(data["created_at"]),
            release_id=data["release_id"],
            model_version=data["model_version"],
            automated_verdict=data["automated_verdict"],
            requested_action=data["requested_action"],
            risk_tier=ReviewTier(data["risk_tier"]),
            risk_categories=data["risk_categories"],
            regression_summary=data["regression_summary"],
            evidence_hash=data["evidence_hash"],
            evidence_artifacts=data["evidence_artifacts"],
            requestor=data["requestor"],
            requestor_justification=data["requestor_justification"],
            sla_deadline=datetime.fromisoformat(data["sla_deadline"]),
            status=ReviewStatus(data["status"]),
            escalation_count=data.get("escalation_count", 0),
            current_assignees=data.get("current_assignees", []),
        )


@dataclass
class HumanReviewDecision:
    """A human reviewer's decision on a review request."""

    decision_id: str
    request_id: str
    decided_at: datetime

    # Decision
    decision: str  # "approve", "reject", "escalate", "defer"
    conditions: list[str]  # Conditions attached to approval

    # Accountability
    reviewer: str
    reviewer_role: str
    reviewer_justification: str

    # Risk acceptance
    accepts_residual_risk: bool
    residual_risk_description: str

    # Audit trail
    decision_hash: str  # SHA256 of decision + evidence

    def to_dict(self) -> dict:
        """Serialize for storage and audit."""
        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "decided_at": self.decided_at.isoformat(),
            "decision": self.decision,
            "conditions": self.conditions,
            "reviewer": self.reviewer,
            "reviewer_role": self.reviewer_role,
            "reviewer_justification": self.reviewer_justification,
            "accepts_residual_risk": self.accepts_residual_risk,
            "residual_risk_description": self.residual_risk_description,
            "decision_hash": self.decision_hash,
        }

    def compute_decision_hash(self) -> str:
        """Compute tamper-evident hash of decision."""
        content = json.dumps({
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "decision": self.decision,
            "reviewer": self.reviewer,
            "justification": self.reviewer_justification,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()


class ReviewQueue:
    """
    Review queue with SLA tracking and escalation.

    In production, this would integrate with:
    - Slack/Teams for notifications
    - PagerDuty for escalations
    - JIRA/Linear for tracking
    """

    def __init__(self, storage_path: str = "data/review_queue.json"):
        self.storage_path = storage_path
        self.pending_reviews: dict[str, HumanReviewRequest] = {}
        self.completed_reviews: dict[str, HumanReviewDecision] = {}

    def submit_review(self, request: HumanReviewRequest) -> str:
        """Submit a new review request."""
        self.pending_reviews[request.request_id] = request
        self._notify_assignees(request)
        return request.request_id

    def get_pending_reviews(self, assignee: Optional[str] = None) -> list[HumanReviewRequest]:
        """Get pending reviews, optionally filtered by assignee."""
        reviews = list(self.pending_reviews.values())
        if assignee:
            reviews = [r for r in reviews if assignee in r.current_assignees]
        return sorted(reviews, key=lambda r: r.sla_deadline)

    def record_decision(self, decision: HumanReviewDecision) -> None:
        """Record a review decision."""
        request = self.pending_reviews.get(decision.request_id)
        if not request:
            raise ValueError(f"Request {decision.request_id} not found")

        # Verify decision hash
        expected_hash = decision.compute_decision_hash()
        if decision.decision_hash != expected_hash:
            raise ValueError("Decision hash mismatch - possible tampering")

        # Update request status
        if decision.decision == "approve":
            request.status = ReviewStatus.APPROVED
        elif decision.decision == "reject":
            request.status = ReviewStatus.REJECTED
        elif decision.decision == "escalate":
            request.status = ReviewStatus.ESCALATED
            self._escalate_review(request)

        self.completed_reviews[decision.decision_id] = decision

        # Move from pending if terminal state
        if request.status in [ReviewStatus.APPROVED, ReviewStatus.REJECTED]:
            del self.pending_reviews[request.request_id]

    def check_sla_breaches(self) -> list[HumanReviewRequest]:
        """Check for reviews that have breached SLA."""
        now = datetime.now()
        breached = []
        for request in self.pending_reviews.values():
            if now > request.sla_deadline and request.status == ReviewStatus.PENDING:
                breached.append(request)
                self._escalate_review(request)
        return breached

    def _notify_assignees(self, request: HumanReviewRequest) -> None:
        """Send notifications to assignees. Mock implementation."""
        print(f"[NOTIFY] Review {request.request_id} assigned to: {request.current_assignees}")
        print(f"         SLA deadline: {request.sla_deadline}")
        print(f"         Risk tier: {request.risk_tier.value}")

    def _escalate_review(self, request: HumanReviewRequest) -> None:
        """Escalate a review to next tier. Mock implementation."""
        request.escalation_count += 1
        request.status = ReviewStatus.ESCALATED
        print(f"[ESCALATE] Review {request.request_id} escalated (count: {request.escalation_count})")


class ReviewWorkflow:
    """
    End-to-end review workflow for release gating.

    This orchestrates the full human-in-the-loop process:
    1. Determine if review is required
    2. Route to appropriate reviewers
    3. Track SLAs and escalate as needed
    4. Record decisions with audit trail
    5. Enforce review requirements for release
    """

    def __init__(
        self,
        requirements: Optional[list[ReviewRequirement]] = None,
        queue: Optional[ReviewQueue] = None,
    ):
        self.requirements = requirements or ReviewRequirement.default_requirements()
        self.queue = queue or ReviewQueue()

    def requires_review(
        self,
        verdict: str,
        risk_categories: list[str],
        statistical_power: float,
        override_requested: bool = False,
        business_risk: str = "NORMAL",
    ) -> Optional[ReviewRequirement]:
        """
        Determine if a release decision requires human review.

        Returns the applicable requirement, or None if no review needed.
        """
        context = {
            "verdict": verdict,
            "risk_categories": risk_categories,
            "statistical_power": statistical_power,
            "override_requested": override_requested,
            "business_risk": business_risk,
            "new_failure_mode_detected": False,  # Would come from analysis
        }

        for req in self.requirements:
            if self._evaluate_condition(req.condition, context):
                return req

        return None

    def _evaluate_condition(self, condition: str, context: dict) -> bool:
        """
        Evaluate a review requirement condition.

        In production, this would use a proper expression evaluator.
        """
        # Simple condition evaluation for demo
        if "verdict == BLOCK AND override_requested" in condition:
            return context["verdict"] == "BLOCK" and context["override_requested"]
        if "verdict == WARN AND business_risk == CRITICAL" in condition:
            return context["verdict"] == "WARN" and context["business_risk"] == "CRITICAL"
        if "statistical_power < 0.80" in condition:
            return context["statistical_power"] < 0.80
        if "new_failure_mode_detected" in condition:
            return context.get("new_failure_mode_detected", False)
        return False

    def create_review_request(
        self,
        release_id: str,
        model_version: str,
        verdict: str,
        regression_summary: dict,
        evidence_artifacts: list[str],
        requestor: str,
        justification: str,
        requirement: ReviewRequirement,
    ) -> HumanReviewRequest:
        """Create a review request with proper SLA and routing."""
        import uuid

        request_id = f"REV-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()

        # Compute evidence hash
        evidence_content = json.dumps(regression_summary, sort_keys=True)
        evidence_hash = hashlib.sha256(evidence_content.encode()).hexdigest()

        # Determine initial assignees based on tier
        assignees = self._get_assignees_for_tier(requirement.tier)

        request = HumanReviewRequest(
            request_id=request_id,
            created_at=now,
            release_id=release_id,
            model_version=model_version,
            automated_verdict=verdict,
            requested_action="override" if verdict == "BLOCK" else "proceed",
            risk_tier=requirement.tier,
            risk_categories=requirement.risk_categories,
            regression_summary=regression_summary,
            evidence_hash=evidence_hash,
            evidence_artifacts=evidence_artifacts,
            requestor=requestor,
            requestor_justification=justification,
            sla_deadline=now + timedelta(hours=requirement.sla_hours),
            current_assignees=assignees,
        )

        self.queue.submit_review(request)
        return request

    def _get_assignees_for_tier(self, tier: ReviewTier) -> list[str]:
        """Get reviewer assignees based on tier."""
        # In production, this would query an org chart / on-call system
        tier_assignees = {
            ReviewTier.TIER_1: ["safety-engineer@company.com"],
            ReviewTier.TIER_2: ["safety-engineer@company.com", "safety-lead@company.com"],
            ReviewTier.TIER_3: ["safety-lead@company.com", "legal@company.com", "vp-eng@company.com"],
            ReviewTier.EMERGENCY: ["safety-lead@company.com", "cto@company.com"],
        }
        return tier_assignees.get(tier, [])

    def can_proceed_with_release(
        self,
        release_id: str,
        verdict: str,
    ) -> tuple[bool, str]:
        """
        Check if a release can proceed.

        Returns (can_proceed, reason).
        """
        # Check if there's a pending review
        for request in self.queue.pending_reviews.values():
            if request.release_id == release_id:
                return False, f"Pending review: {request.request_id}"

        # Check if there's an approved override
        for decision in self.queue.completed_reviews.values():
            request = self._get_request_for_decision(decision)
            if request and request.release_id == release_id:
                if decision.decision == "approve":
                    return True, f"Approved by: {decision.reviewer}"
                elif decision.decision == "reject":
                    return False, f"Rejected by: {decision.reviewer}"

        # No review required or pending
        if verdict == "OK":
            return True, "Automated verdict: OK"
        elif verdict == "WARN":
            return True, "Automated verdict: WARN (proceed with caution)"
        else:
            return False, "Automated verdict: BLOCK (requires review to override)"

    def _get_request_for_decision(self, decision: HumanReviewDecision) -> Optional[HumanReviewRequest]:
        """Get the original request for a decision."""
        # Would query storage in production
        return None


# Example usage and demonstration
if __name__ == "__main__":
    # Initialize workflow
    workflow = ReviewWorkflow()

    # Example: BLOCK verdict with override requested
    requirement = workflow.requires_review(
        verdict="BLOCK",
        risk_categories=["coordinated_misuse"],
        statistical_power=0.85,
        override_requested=True,
        business_risk="CRITICAL",
    )

    if requirement:
        print(f"\nReview required: {requirement.tier.value}")
        print(f"SLA: {requirement.sla_hours} hours")
        print(f"Escalation path: {requirement.escalation_path}")

        # Create review request
        request = workflow.create_review_request(
            release_id="release-2026-02-01",
            model_version="claude-3.6",
            verdict="BLOCK",
            regression_summary={
                "violation_rate": {"baseline": 0.08, "candidate": 0.12, "delta": 0.04},
                "delayed_failure_rate": {"baseline": 0.21, "candidate": 0.34, "delta": 0.13},
            },
            evidence_artifacts=["reports/regression_report.html", "data/traces.jsonl"],
            requestor="release-engineer@company.com",
            justification="Critical product launch; mitigation monitoring in place",
            requirement=requirement,
        )

        print(f"\nCreated review request: {request.request_id}")
        print(f"Assigned to: {request.current_assignees}")
        print(f"SLA deadline: {request.sla_deadline}")
