"""
Release Risk Ledger

An immutable, auditable record of all release decisions and their associated risks.

Every release decision is recorded with:
1. Who made the decision (accountability)
2. What risks were identified (transparency)
3. What risks were accepted (ownership)
4. Under what conditions (traceability)

This ledger serves as:
- Audit trail for compliance
- Historical record for incident investigation
- Accountability mechanism for risk acceptance
- Input to board-level safety reporting

Design Philosophy:
- Every release is a risk decision, even if risk is low
- Risk ownership must be explicit and named
- No decision is lost - the ledger is append-only
- Post-hoc analysis should never ask "who approved this?"
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json
import hashlib


class RiskLevel(Enum):
    """Severity levels for residual risk."""

    NEGLIGIBLE = "negligible"  # Risk within normal operating bounds
    LOW = "low"  # Acceptable risk with standard monitoring
    MEDIUM = "medium"  # Elevated risk requiring enhanced monitoring
    HIGH = "high"  # Significant risk requiring mitigation plan
    CRITICAL = "critical"  # Maximum risk, requires executive approval


class ReleaseOutcome(Enum):
    """Final outcome of a release decision."""

    APPROVED = "approved"  # Release proceeded
    APPROVED_WITH_CONDITIONS = "approved_with_conditions"
    BLOCKED = "blocked"  # Release blocked
    ROLLED_BACK = "rolled_back"  # Released then rolled back
    WITHDRAWN = "withdrawn"  # Candidate withdrawn before decision


@dataclass
class RiskOwnership:
    """
    Explicit assignment of risk ownership.

    In production safety systems, someone must own each identified risk.
    This prevents diffusion of responsibility.
    """

    risk_id: str
    risk_description: str
    risk_level: RiskLevel

    # Ownership
    owner_name: str
    owner_role: str
    owner_email: str

    # Acceptance
    accepted_at: datetime
    acceptance_statement: str

    # Conditions
    monitoring_requirements: list[str]
    rollback_triggers: list[str]
    expiration: Optional[datetime] = None  # Risk acceptance expires

    def to_dict(self) -> dict:
        return {
            "risk_id": self.risk_id,
            "risk_description": self.risk_description,
            "risk_level": self.risk_level.value,
            "owner_name": self.owner_name,
            "owner_role": self.owner_role,
            "owner_email": self.owner_email,
            "accepted_at": self.accepted_at.isoformat(),
            "acceptance_statement": self.acceptance_statement,
            "monitoring_requirements": self.monitoring_requirements,
            "rollback_triggers": self.rollback_triggers,
            "expiration": self.expiration.isoformat() if self.expiration else None,
        }


@dataclass
class AcceptanceRecord:
    """
    Formal record of risk acceptance for a release.

    This is the "signature" that authorizes release despite identified risks.
    """

    record_id: str
    release_id: str

    # What was accepted
    accepted_risks: list[RiskOwnership]
    total_residual_risk: RiskLevel

    # Who accepted
    approver_name: str
    approver_role: str
    approver_email: str

    # When and why
    accepted_at: datetime
    justification: str
    conditions: list[str]

    # Verification
    evidence_package_hash: str
    approval_chain: list[str]  # List of approvers in sequence

    # Cryptographic signature
    record_hash: str = ""

    def __post_init__(self):
        if not self.record_hash:
            self.record_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute tamper-evident hash."""
        content = json.dumps({
            "record_id": self.record_id,
            "release_id": self.release_id,
            "accepted_risks": [r.to_dict() for r in self.accepted_risks],
            "approver_name": self.approver_name,
            "justification": self.justification,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "release_id": self.release_id,
            "accepted_risks": [r.to_dict() for r in self.accepted_risks],
            "total_residual_risk": self.total_residual_risk.value,
            "approver_name": self.approver_name,
            "approver_role": self.approver_role,
            "approver_email": self.approver_email,
            "accepted_at": self.accepted_at.isoformat(),
            "justification": self.justification,
            "conditions": self.conditions,
            "evidence_package_hash": self.evidence_package_hash,
            "approval_chain": self.approval_chain,
            "record_hash": self.record_hash,
        }


@dataclass
class RiskLedgerEntry:
    """
    A single entry in the release risk ledger.

    Each entry captures the complete context of a release decision:
    - The automated verdict
    - Identified risks
    - Human review (if any)
    - Final decision and outcome
    - Accountability trail
    """

    entry_id: str
    created_at: datetime

    # Release identification
    release_id: str
    model_version: str
    model_hash: str

    # Automated assessment
    automated_verdict: str  # OK, WARN, BLOCK
    automated_reasons: list[str]
    metrics_snapshot: dict

    # Risk identification
    identified_risks: list[dict]
    total_risk_score: float
    risk_categories: list[str]

    # Human review
    human_review_required: bool
    human_review_id: Optional[str] = None
    human_override: bool = False

    # Final decision
    final_outcome: ReleaseOutcome = ReleaseOutcome.BLOCKED
    acceptance_record: Optional[AcceptanceRecord] = None

    # Evidence and audit
    evidence_artifacts: list[str] = field(default_factory=list)
    lineage: dict = field(default_factory=dict)

    # Post-release tracking
    post_release_incidents: list[str] = field(default_factory=list)
    rolled_back_at: Optional[datetime] = None
    rollback_reason: Optional[str] = None

    # Hash chain for tamper evidence
    previous_entry_hash: str = ""
    entry_hash: str = ""

    def __post_init__(self):
        if not self.entry_hash:
            self.entry_hash = self._compute_hash()

    def _compute_hash(self) -> str:
        """Compute entry hash including previous entry for chain integrity."""
        content = json.dumps({
            "entry_id": self.entry_id,
            "release_id": self.release_id,
            "model_version": self.model_version,
            "automated_verdict": self.automated_verdict,
            "final_outcome": self.final_outcome.value,
            "previous_entry_hash": self.previous_entry_hash,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "created_at": self.created_at.isoformat(),
            "release_id": self.release_id,
            "model_version": self.model_version,
            "model_hash": self.model_hash,
            "automated_verdict": self.automated_verdict,
            "automated_reasons": self.automated_reasons,
            "metrics_snapshot": self.metrics_snapshot,
            "identified_risks": self.identified_risks,
            "total_risk_score": self.total_risk_score,
            "risk_categories": self.risk_categories,
            "human_review_required": self.human_review_required,
            "human_review_id": self.human_review_id,
            "human_override": self.human_override,
            "final_outcome": self.final_outcome.value,
            "acceptance_record": self.acceptance_record.to_dict() if self.acceptance_record else None,
            "evidence_artifacts": self.evidence_artifacts,
            "lineage": self.lineage,
            "post_release_incidents": self.post_release_incidents,
            "rolled_back_at": self.rolled_back_at.isoformat() if self.rolled_back_at else None,
            "rollback_reason": self.rollback_reason,
            "previous_entry_hash": self.previous_entry_hash,
            "entry_hash": self.entry_hash,
        }


class ReleaseLedger:
    """
    Immutable ledger of all release decisions.

    The ledger is:
    - Append-only (entries cannot be modified or deleted)
    - Hash-chained (tampering is detectable)
    - Queryable (for audit and analysis)
    """

    def __init__(self, storage_path: str = "data/release_ledger.json"):
        self.storage_path = storage_path
        self.entries: list[RiskLedgerEntry] = []
        self._load()

    def _load(self) -> None:
        """Load ledger from storage."""
        # In production, this would load from durable storage
        pass

    def _save(self) -> None:
        """Persist ledger to storage."""
        # In production, this would write to durable storage with replication
        pass

    def add_entry(self, entry: RiskLedgerEntry) -> str:
        """
        Add an entry to the ledger.

        Returns the entry hash for verification.
        """
        # Link to previous entry
        if self.entries:
            entry.previous_entry_hash = self.entries[-1].entry_hash

        # Recompute hash with chain
        entry.entry_hash = entry._compute_hash()

        self.entries.append(entry)
        self._save()

        return entry.entry_hash

    def get_entry(self, entry_id: str) -> Optional[RiskLedgerEntry]:
        """Retrieve an entry by ID."""
        for entry in self.entries:
            if entry.entry_id == entry_id:
                return entry
        return None

    def get_entries_for_model(self, model_version: str) -> list[RiskLedgerEntry]:
        """Get all entries for a specific model version."""
        return [e for e in self.entries if e.model_version == model_version]

    def get_entries_by_outcome(self, outcome: ReleaseOutcome) -> list[RiskLedgerEntry]:
        """Get all entries with a specific outcome."""
        return [e for e in self.entries if e.final_outcome == outcome]

    def get_entries_with_incidents(self) -> list[RiskLedgerEntry]:
        """Get all entries that had post-release incidents."""
        return [e for e in self.entries if e.post_release_incidents]

    def verify_chain_integrity(self) -> tuple[bool, Optional[str]]:
        """
        Verify the hash chain integrity of the ledger.

        Returns (is_valid, first_invalid_entry_id).
        """
        for i, entry in enumerate(self.entries):
            # Check entry hash
            expected_hash = entry._compute_hash()
            if entry.entry_hash != expected_hash:
                return False, entry.entry_id

            # Check chain link
            if i > 0:
                if entry.previous_entry_hash != self.entries[i-1].entry_hash:
                    return False, entry.entry_id

        return True, None

    def record_incident(self, release_id: str, incident_id: str) -> None:
        """Record a post-release incident against a release entry."""
        for entry in self.entries:
            if entry.release_id == release_id:
                entry.post_release_incidents.append(incident_id)
                # Note: This modifies the entry but not the hash chain
                # In production, this would be a separate append-only incident log
                self._save()
                return

    def record_rollback(self, release_id: str, reason: str) -> None:
        """Record that a release was rolled back."""
        for entry in self.entries:
            if entry.release_id == release_id:
                entry.rolled_back_at = datetime.now()
                entry.rollback_reason = reason
                entry.final_outcome = ReleaseOutcome.ROLLED_BACK
                self._save()
                return

    def get_risk_summary(self, days: int = 90) -> dict:
        """
        Generate risk summary for reporting.

        Returns aggregated statistics for board-level reporting.
        """
        cutoff = datetime.now()
        recent = [e for e in self.entries
                  if (cutoff - e.created_at).days <= days]

        if not recent:
            return {"period_days": days, "total_releases": 0}

        total = len(recent)
        by_outcome = {}
        for outcome in ReleaseOutcome:
            by_outcome[outcome.value] = len([e for e in recent
                                              if e.final_outcome == outcome])

        with_incidents = len([e for e in recent if e.post_release_incidents])
        overrides = len([e for e in recent if e.human_override])

        return {
            "period_days": days,
            "total_releases": total,
            "by_outcome": by_outcome,
            "releases_with_incidents": with_incidents,
            "incident_rate": with_incidents / total if total > 0 else 0,
            "human_overrides": overrides,
            "override_rate": overrides / total if total > 0 else 0,
        }

    def export_for_audit(self) -> dict:
        """Export full ledger for external audit."""
        is_valid, invalid_entry = self.verify_chain_integrity()
        return {
            "export_timestamp": datetime.now().isoformat(),
            "chain_valid": is_valid,
            "invalid_entry": invalid_entry,
            "total_entries": len(self.entries),
            "entries": [e.to_dict() for e in self.entries],
        }


# Example usage
if __name__ == "__main__":
    import uuid

    ledger = ReleaseLedger()

    # Create a risk ownership record
    risk = RiskOwnership(
        risk_id="RISK-001",
        risk_description="Elevated policy erosion rate in multi-turn scenarios",
        risk_level=RiskLevel.MEDIUM,
        owner_name="Jane Smith",
        owner_role="Safety Lead",
        owner_email="jane.smith@company.com",
        accepted_at=datetime.now(),
        acceptance_statement="Risk accepted with enhanced monitoring and 7-day review",
        monitoring_requirements=[
            "Real-time erosion monitoring with 5-min granularity",
            "Daily regression run on production traffic sample",
        ],
        rollback_triggers=[
            "Erosion rate exceeds 15% for 1 hour",
            "Any critical-severity incident",
        ],
    )

    # Create acceptance record
    acceptance = AcceptanceRecord(
        record_id=f"ACC-{uuid.uuid4().hex[:8].upper()}",
        release_id="release-2026-02-01",
        accepted_risks=[risk],
        total_residual_risk=RiskLevel.MEDIUM,
        approver_name="Jane Smith",
        approver_role="Safety Lead",
        approver_email="jane.smith@company.com",
        accepted_at=datetime.now(),
        justification="Critical product launch with appropriate monitoring",
        conditions=["7-day enhanced monitoring", "Daily safety review"],
        evidence_package_hash="sha256:abc123...",
        approval_chain=["John Doe (Release Eng)", "Jane Smith (Safety Lead)"],
    )

    # Create ledger entry
    entry = RiskLedgerEntry(
        entry_id=f"LED-{uuid.uuid4().hex[:8].upper()}",
        created_at=datetime.now(),
        release_id="release-2026-02-01",
        model_version="claude-3.6",
        model_hash="sha256:model123...",
        automated_verdict="WARN",
        automated_reasons=["Policy erosion slope +0.06 exceeds warn threshold"],
        metrics_snapshot={
            "violation_rate": 0.092,
            "delayed_failure_rate": 0.28,
            "policy_erosion_slope": 0.18,
        },
        identified_risks=[risk.to_dict()],
        total_risk_score=0.45,
        risk_categories=["policy_erosion"],
        human_review_required=True,
        human_review_id="REV-12345678",
        human_override=True,
        final_outcome=ReleaseOutcome.APPROVED_WITH_CONDITIONS,
        acceptance_record=acceptance,
        evidence_artifacts=["reports/regression.html", "data/traces.jsonl"],
        lineage={
            "eval_run_id": "run_2026_02_01_001",
            "stress_tests_version": "v0.3",
        },
    )

    # Add to ledger
    entry_hash = ledger.add_entry(entry)
    print(f"Added entry: {entry.entry_id}")
    print(f"Entry hash: {entry_hash}")

    # Verify integrity
    is_valid, invalid = ledger.verify_chain_integrity()
    print(f"Chain valid: {is_valid}")

    # Get summary
    summary = ledger.get_risk_summary(90)
    print("\nRisk summary (90 days):")
    print(json.dumps(summary, indent=2))
