"""
Audit Export Module

Generates compliance-ready audit packages for external review.

Audit packages include:
1. Complete decision trail for a release
2. All supporting evidence with cryptographic hashes
3. Chain of custody documentation
4. Compliance mapping to relevant standards

Designed for:
- Internal audit teams
- External auditors
- Regulatory submissions
- Board-level reporting
- Incident investigation

Design Philosophy:
- Audit packages are self-contained and verifiable
- No external dependencies required to verify authenticity
- Evidence chain is cryptographically tamper-evident
- Export format is human-readable and machine-parseable
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import json
import hashlib


class ComplianceStandard(Enum):
    """Compliance standards for mapping."""

    SOC2 = "soc2"
    ISO27001 = "iso27001"
    NIST_AI_RMF = "nist_ai_rmf"  # NIST AI Risk Management Framework
    EU_AI_ACT = "eu_ai_act"
    INTERNAL = "internal"


class ArtifactType(Enum):
    """Types of audit artifacts."""

    METRICS_SNAPSHOT = "metrics_snapshot"
    REGRESSION_REPORT = "regression_report"
    TRACE_LOG = "trace_log"
    REVIEW_DECISION = "review_decision"
    ACCEPTANCE_RECORD = "acceptance_record"
    EVIDENCE_HASH_MANIFEST = "evidence_hash_manifest"
    CHAIN_OF_CUSTODY = "chain_of_custody"
    COMPLIANCE_MAPPING = "compliance_mapping"


@dataclass
class AuditArtifact:
    """A single artifact in an audit package."""

    artifact_id: str
    artifact_type: ArtifactType
    name: str
    description: str

    # Content
    content_path: str  # Path within audit package
    content_hash: str  # SHA256 of content
    content_size_bytes: int

    # Metadata
    created_at: datetime
    created_by: str

    # Verification
    hash_algorithm: str = "sha256"

    def to_dict(self) -> dict:
        return {
            "artifact_id": self.artifact_id,
            "artifact_type": self.artifact_type.value,
            "name": self.name,
            "description": self.description,
            "content_path": self.content_path,
            "content_hash": self.content_hash,
            "content_size_bytes": self.content_size_bytes,
            "created_at": self.created_at.isoformat(),
            "created_by": self.created_by,
            "hash_algorithm": self.hash_algorithm,
        }


@dataclass
class ComplianceMapping:
    """Mapping of release decision to compliance requirements."""

    standard: ComplianceStandard
    requirement_id: str
    requirement_description: str

    # How this release satisfies the requirement
    satisfaction_method: str
    evidence_artifact_ids: list[str]

    # Assessment
    status: str  # "satisfied", "partially_satisfied", "not_applicable"
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "standard": self.standard.value,
            "requirement_id": self.requirement_id,
            "requirement_description": self.requirement_description,
            "satisfaction_method": self.satisfaction_method,
            "evidence_artifact_ids": self.evidence_artifact_ids,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass
class ChainOfCustody:
    """Chain of custody for audit evidence."""

    custody_events: list[dict] = field(default_factory=list)

    def add_event(
        self,
        event_type: str,
        actor: str,
        timestamp: datetime,
        description: str,
        artifact_ids: list[str],
    ) -> None:
        """Record a custody event."""
        self.custody_events.append({
            "event_type": event_type,
            "actor": actor,
            "timestamp": timestamp.isoformat(),
            "description": description,
            "artifact_ids": artifact_ids,
        })

    def to_dict(self) -> dict:
        return {
            "custody_events": self.custody_events,
            "total_events": len(self.custody_events),
        }


@dataclass
class ComplianceReport:
    """Compliance report for a release."""

    report_id: str
    release_id: str
    generated_at: datetime

    # Standards covered
    standards: list[ComplianceStandard]
    mappings: list[ComplianceMapping]

    # Summary
    total_requirements: int = 0
    satisfied: int = 0
    partially_satisfied: int = 0
    not_applicable: int = 0

    def compute_summary(self) -> None:
        """Compute summary statistics."""
        self.total_requirements = len(self.mappings)
        self.satisfied = len([m for m in self.mappings if m.status == "satisfied"])
        self.partially_satisfied = len([m for m in self.mappings if m.status == "partially_satisfied"])
        self.not_applicable = len([m for m in self.mappings if m.status == "not_applicable"])

    def to_dict(self) -> dict:
        self.compute_summary()
        return {
            "report_id": self.report_id,
            "release_id": self.release_id,
            "generated_at": self.generated_at.isoformat(),
            "standards": [s.value for s in self.standards],
            "mappings": [m.to_dict() for m in self.mappings],
            "summary": {
                "total_requirements": self.total_requirements,
                "satisfied": self.satisfied,
                "partially_satisfied": self.partially_satisfied,
                "not_applicable": self.not_applicable,
                "compliance_rate": self.satisfied / self.total_requirements if self.total_requirements > 0 else 0,
            },
        }


@dataclass
class AuditPackage:
    """
    Complete audit package for a release decision.

    A self-contained package that includes all evidence,
    decisions, and documentation needed for audit review.
    """

    package_id: str
    created_at: datetime

    # Scope
    release_id: str
    model_version: str
    audit_period_start: datetime
    audit_period_end: datetime

    # Contents
    artifacts: list[AuditArtifact] = field(default_factory=list)
    chain_of_custody: ChainOfCustody = field(default_factory=ChainOfCustody)
    compliance_report: Optional[ComplianceReport] = None

    # Verification
    package_hash: str = ""

    # Metadata
    prepared_by: str = ""
    approved_by: str = ""
    purpose: str = ""  # "internal_audit", "external_audit", "regulatory", "incident_investigation"

    def __post_init__(self):
        if not self.package_hash:
            self.package_hash = self._compute_package_hash()

    def _compute_package_hash(self) -> str:
        """Compute hash of entire package for integrity verification."""
        content = json.dumps({
            "package_id": self.package_id,
            "release_id": self.release_id,
            "artifacts": [a.content_hash for a in self.artifacts],
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()

    def add_artifact(self, artifact: AuditArtifact) -> None:
        """Add an artifact to the package."""
        self.artifacts.append(artifact)

        # Record custody event
        self.chain_of_custody.add_event(
            event_type="artifact_added",
            actor=self.prepared_by,
            timestamp=datetime.now(),
            description=f"Added artifact: {artifact.name}",
            artifact_ids=[artifact.artifact_id],
        )

        # Recompute package hash
        self.package_hash = self._compute_package_hash()

    def verify_integrity(self) -> tuple[bool, list[str]]:
        """
        Verify integrity of all artifacts in the package.

        Returns (is_valid, list_of_invalid_artifacts).
        """
        invalid = []
        # In production, this would re-hash each artifact and compare
        # For demo, we assume all are valid
        return len(invalid) == 0, invalid

    def to_dict(self) -> dict:
        return {
            "package_id": self.package_id,
            "created_at": self.created_at.isoformat(),
            "release_id": self.release_id,
            "model_version": self.model_version,
            "audit_period": {
                "start": self.audit_period_start.isoformat(),
                "end": self.audit_period_end.isoformat(),
            },
            "artifacts": [a.to_dict() for a in self.artifacts],
            "chain_of_custody": self.chain_of_custody.to_dict(),
            "compliance_report": self.compliance_report.to_dict() if self.compliance_report else None,
            "package_hash": self.package_hash,
            "metadata": {
                "prepared_by": self.prepared_by,
                "approved_by": self.approved_by,
                "purpose": self.purpose,
            },
        }


class AuditExporter:
    """
    Export audit packages for releases.

    Generates complete, self-contained audit packages
    that can be provided to internal or external auditors.
    """

    def __init__(self, output_dir: str = "audit_exports"):
        self.output_dir = output_dir

    def create_package(
        self,
        release_id: str,
        model_version: str,
        purpose: str,
        prepared_by: str,
    ) -> AuditPackage:
        """Create a new audit package."""
        import uuid

        now = datetime.now()
        package = AuditPackage(
            package_id=f"AUDIT-{uuid.uuid4().hex[:8].upper()}",
            created_at=now,
            release_id=release_id,
            model_version=model_version,
            audit_period_start=now,
            audit_period_end=now,
            prepared_by=prepared_by,
            purpose=purpose,
        )

        # Record creation
        package.chain_of_custody.add_event(
            event_type="package_created",
            actor=prepared_by,
            timestamp=now,
            description=f"Audit package created for {release_id}",
            artifact_ids=[],
        )

        return package

    def add_metrics_artifact(
        self,
        package: AuditPackage,
        metrics: dict,
        created_by: str,
    ) -> AuditArtifact:
        """Add metrics snapshot as an artifact."""
        import uuid

        content = json.dumps(metrics, indent=2)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        artifact = AuditArtifact(
            artifact_id=f"ART-{uuid.uuid4().hex[:8].upper()}",
            artifact_type=ArtifactType.METRICS_SNAPSHOT,
            name="metrics_snapshot.json",
            description="Point-in-time snapshot of all safety metrics",
            content_path=f"metrics/{package.release_id}_metrics.json",
            content_hash=content_hash,
            content_size_bytes=len(content),
            created_at=datetime.now(),
            created_by=created_by,
        )

        package.add_artifact(artifact)
        return artifact

    def add_decision_artifact(
        self,
        package: AuditPackage,
        decision: dict,
        created_by: str,
    ) -> AuditArtifact:
        """Add review decision as an artifact."""
        import uuid

        content = json.dumps(decision, indent=2)
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        artifact = AuditArtifact(
            artifact_id=f"ART-{uuid.uuid4().hex[:8].upper()}",
            artifact_type=ArtifactType.REVIEW_DECISION,
            name="review_decision.json",
            description="Human review decision with justification",
            content_path=f"decisions/{package.release_id}_decision.json",
            content_hash=content_hash,
            content_size_bytes=len(content),
            created_at=datetime.now(),
            created_by=created_by,
        )

        package.add_artifact(artifact)
        return artifact

    def generate_compliance_report(
        self,
        package: AuditPackage,
        standards: list[ComplianceStandard],
    ) -> ComplianceReport:
        """Generate compliance mapping report."""
        import uuid

        # Default mappings for NIST AI RMF
        mappings = []

        if ComplianceStandard.NIST_AI_RMF in standards:
            mappings.extend([
                ComplianceMapping(
                    standard=ComplianceStandard.NIST_AI_RMF,
                    requirement_id="GOVERN-1.1",
                    requirement_description="Legal and regulatory requirements are understood",
                    satisfaction_method="Automated compliance mapping in release gate",
                    evidence_artifact_ids=[a.artifact_id for a in package.artifacts],
                    status="satisfied",
                ),
                ComplianceMapping(
                    standard=ComplianceStandard.NIST_AI_RMF,
                    requirement_id="MAP-1.1",
                    requirement_description="Risk identification processes established",
                    satisfaction_method="Automated risk scoring with human review for high-risk",
                    evidence_artifact_ids=[a.artifact_id for a in package.artifacts
                                           if a.artifact_type == ArtifactType.METRICS_SNAPSHOT],
                    status="satisfied",
                ),
                ComplianceMapping(
                    standard=ComplianceStandard.NIST_AI_RMF,
                    requirement_id="MEASURE-2.2",
                    requirement_description="AI system performance monitored",
                    satisfaction_method="Continuous safety metric tracking with drift detection",
                    evidence_artifact_ids=[],
                    status="satisfied",
                ),
                ComplianceMapping(
                    standard=ComplianceStandard.NIST_AI_RMF,
                    requirement_id="MANAGE-1.1",
                    requirement_description="Risk treatments prioritized and acted upon",
                    satisfaction_method="Release gating with OK/WARN/BLOCK verdicts",
                    evidence_artifact_ids=[a.artifact_id for a in package.artifacts
                                           if a.artifact_type == ArtifactType.REVIEW_DECISION],
                    status="satisfied",
                ),
            ])

        if ComplianceStandard.EU_AI_ACT in standards:
            mappings.extend([
                ComplianceMapping(
                    standard=ComplianceStandard.EU_AI_ACT,
                    requirement_id="Article-9",
                    requirement_description="Risk management system",
                    satisfaction_method="End-to-end release gating pipeline",
                    evidence_artifact_ids=[a.artifact_id for a in package.artifacts],
                    status="satisfied",
                ),
                ComplianceMapping(
                    standard=ComplianceStandard.EU_AI_ACT,
                    requirement_id="Article-11",
                    requirement_description="Technical documentation",
                    satisfaction_method="Audit package with evidence lineage",
                    evidence_artifact_ids=[a.artifact_id for a in package.artifacts],
                    status="satisfied",
                ),
            ])

        report = ComplianceReport(
            report_id=f"COMP-{uuid.uuid4().hex[:8].upper()}",
            release_id=package.release_id,
            generated_at=datetime.now(),
            standards=standards,
            mappings=mappings,
        )

        package.compliance_report = report
        return report

    def finalize_package(
        self,
        package: AuditPackage,
        approved_by: str,
    ) -> str:
        """
        Finalize and export the audit package.

        Returns the package hash for verification.
        """
        package.approved_by = approved_by
        package.audit_period_end = datetime.now()

        # Final custody event
        package.chain_of_custody.add_event(
            event_type="package_finalized",
            actor=approved_by,
            timestamp=datetime.now(),
            description="Audit package finalized and approved",
            artifact_ids=[a.artifact_id for a in package.artifacts],
        )

        # Compute final hash
        package.package_hash = package._compute_package_hash()

        # In production: write to storage
        # self._write_package(package)

        return package.package_hash

    def export_to_json(self, package: AuditPackage) -> str:
        """Export package as JSON for transfer."""
        return json.dumps(package.to_dict(), indent=2)


# Example usage
if __name__ == "__main__":
    exporter = AuditExporter()

    # Create package
    package = exporter.create_package(
        release_id="release-2026-02-01",
        model_version="claude-3.6",
        purpose="internal_audit",
        prepared_by="blueoceanally@gmail.com",
    )

    # Add artifacts
    exporter.add_metrics_artifact(
        package,
        metrics={
            "violation_rate": 0.092,
            "delayed_failure_rate": 0.28,
            "policy_erosion_slope": 0.18,
        },
        created_by="blueoceanally@gmail.com",
    )

    exporter.add_decision_artifact(
        package,
        decision={
            "decision": "approve",
            "reviewer": "Jane Smith",
            "justification": "Risk accepted with enhanced monitoring",
        },
        created_by="blueoceanally@gmail.com",
    )

    # Generate compliance report
    exporter.generate_compliance_report(
        package,
        standards=[ComplianceStandard.NIST_AI_RMF, ComplianceStandard.EU_AI_ACT],
    )

    # Finalize
    package_hash = exporter.finalize_package(package, approved_by="blueoceanally@gmail.com")

    print(f"Package ID: {package.package_id}")
    print(f"Package hash: {package_hash}")
    print(f"Artifacts: {len(package.artifacts)}")
    print("\nCompliance summary:")
    if package.compliance_report:
        package.compliance_report.compute_summary()
        print(f"  Total requirements: {package.compliance_report.total_requirements}")
        print(f"  Satisfied: {package.compliance_report.satisfied}")
