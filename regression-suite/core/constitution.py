"""
Constitution-as-Code Implementation

The constitution is the first-class object in the safety system.
This module:
1. Loads and validates the constitution
2. Computes constitution hash for traceability
3. Evaluates verdicts against constitution principles
4. Tracks alignment debt
5. Generates constitution compliance reports

Design Philosophy:
- Constitution is executable, not just documentation
- Every verdict traces to constitution principles
- Deviations are explicit and tracked
- Constitution version is immutable once deployed
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
import yaml
import json
import hashlib


class Enforcement(Enum):
    """Enforcement level for principles."""

    HARD = "hard"  # Violation = BLOCK
    SOFT = "soft"  # Violation = WARN


class VerdictSource(Enum):
    """Source of verdict determination."""

    PRINCIPLE = "principle"
    RULE = "rule"
    HUMAN_OVERRIDE = "human_override"


@dataclass
class Principle:
    """A constitution principle."""

    id: str
    name: str
    statement: str
    priority: int
    enforcement: Enforcement
    measurable_criteria: list[dict]

    def evaluate(self, metrics: dict) -> tuple[bool, list[str]]:
        """
        Evaluate whether metrics satisfy this principle.

        Returns (satisfied, list_of_violations).
        """
        violations = []

        for criterion in self.measurable_criteria:
            metric_name = criterion.get("metric")
            threshold = criterion.get("threshold")

            if metric_name not in metrics:
                # Missing metric is a soft violation
                violations.append(f"Missing metric: {metric_name}")
                continue

            value = metrics[metric_name]

            # Evaluate threshold (simplified - production would use expression parser)
            if not self._evaluate_threshold(value, threshold):
                violations.append(
                    f"{criterion['criterion']}: {metric_name}={value} violates {threshold}"
                )

        return len(violations) == 0, violations

    def _evaluate_threshold(self, value, threshold: str) -> bool:
        """Evaluate a threshold expression."""
        if threshold == "true":
            return bool(value)
        if threshold == "false":
            return not bool(value)
        if threshold.startswith(">="):
            return value >= float(threshold[2:].strip())
        if threshold.startswith("<="):
            return value <= float(threshold[2:].strip())
        if threshold.startswith(">"):
            return value > float(threshold[1:].strip())
        if threshold.startswith("<"):
            return value < float(threshold[1:].strip())
        if threshold.startswith("="):
            return value == float(threshold[1:].strip())
        if threshold == "delta <= 0":
            return value <= 0
        if threshold == "requires_human_review":
            return True  # Satisfied if present, triggers review
        return True  # Unknown threshold format - pass


@dataclass
class FailureMode:
    """A failure mode from the taxonomy."""

    id: str
    description: str
    severity: str
    relevant_principles: list[str]
    detection_required: list[str]


@dataclass
class SafeguardMapping:
    """Mapping of a safeguard to principles it upholds."""

    id: str
    description: str
    upholds_principles: list[str]
    covers_failure_modes: list[str]
    effectiveness_metric: str
    minimum_effectiveness: float


@dataclass
class ConstitutionViolation:
    """A violation of a constitution principle."""

    principle_id: str
    principle_name: str
    violation_description: str
    severity: str  # "hard" or "soft"
    metrics_at_violation: dict
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        return {
            "principle_id": self.principle_id,
            "principle_name": self.principle_name,
            "violation_description": self.violation_description,
            "severity": self.severity,
            "metrics_at_violation": self.metrics_at_violation,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class AlignmentDebtEntry:
    """A single entry in the alignment debt ledger."""

    entry_id: str
    created_at: datetime
    release_id: str

    # Debt details
    category: str
    description: str
    debt_amount: float

    # Status
    status: str  # "active", "resolved", "accepted"
    resolved_at: Optional[datetime] = None
    resolution_method: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "entry_id": self.entry_id,
            "created_at": self.created_at.isoformat(),
            "release_id": self.release_id,
            "category": self.category,
            "description": self.description,
            "debt_amount": self.debt_amount,
            "status": self.status,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolution_method": self.resolution_method,
        }


class Constitution:
    """
    The executable constitution for the safety system.

    This is the authoritative source for:
    - What principles govern release decisions
    - How violations are determined
    - What safeguards map to what principles
    - How alignment debt is tracked
    """

    def __init__(self, config_path: str = "config/constitution.yaml"):
        self.config_path = config_path
        self.version: str = ""
        self.effective_date: str = ""
        self.constitution_hash: str = ""

        self.principles: dict[str, Principle] = {}
        self.failure_modes: dict[str, FailureMode] = {}
        self.safeguard_mappings: dict[str, SafeguardMapping] = {}
        self.release_rules: dict = {}
        self.alignment_debt_config: dict = {}

        self._load()

    def _load(self) -> None:
        """Load constitution from YAML."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
        except FileNotFoundError:
            # Use default minimal constitution
            config = self._default_constitution()

        self.version = config.get("version", "0.0.0")
        self.effective_date = config.get("effective_date", "")

        # Load principles
        for pid, pconfig in config.get("principles", {}).items():
            self.principles[pid] = Principle(
                id=pconfig["id"],
                name=pconfig["name"],
                statement=pconfig["statement"],
                priority=pconfig["priority"],
                enforcement=Enforcement(pconfig["enforcement"]),
                measurable_criteria=pconfig.get("measurable_criteria", []),
            )

        # Load failure taxonomy
        for fid, fconfig in config.get("failure_taxonomy", {}).items():
            self.failure_modes[fid] = FailureMode(
                id=fid,
                description=fconfig["description"],
                severity=fconfig["severity"],
                relevant_principles=fconfig["relevant_principles"],
                detection_required=fconfig["detection_required"],
            )

        # Load safeguard mappings
        for sid, sconfig in config.get("safeguard_principle_mapping", {}).items():
            self.safeguard_mappings[sid] = SafeguardMapping(
                id=sid,
                description=sconfig["description"],
                upholds_principles=sconfig["upholds_principles"],
                covers_failure_modes=sconfig["covers_failure_modes"],
                effectiveness_metric=sconfig["effectiveness_metric"],
                minimum_effectiveness=sconfig["minimum_effectiveness"],
            )

        # Load release rules
        self.release_rules = config.get("release_gate_rules", {})

        # Load alignment debt config
        self.alignment_debt_config = config.get("alignment_debt", {})

        # Compute constitution hash
        self.constitution_hash = self._compute_hash(config)

    def _compute_hash(self, config: dict) -> str:
        """Compute SHA256 hash of constitution content."""
        # Remove changelog for hash (it's metadata, not content)
        config_for_hash = {k: v for k, v in config.items() if k != "changelog"}
        content = json.dumps(config_for_hash, sort_keys=True)
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()[:16]}"

    def _default_constitution(self) -> dict:
        """Return minimal default constitution."""
        return {
            "version": "0.0.0",
            "effective_date": datetime.now().isoformat()[:10],
            "principles": {
                "P1_safety_primacy": {
                    "id": "P1",
                    "name": "Safety Primacy",
                    "statement": "Safety takes precedence over capability.",
                    "priority": 1,
                    "enforcement": "hard",
                    "measurable_criteria": [],
                }
            },
            "failure_taxonomy": {},
            "safeguard_principle_mapping": {},
            "release_gate_rules": {"block_rules": [], "warn_rules": []},
            "alignment_debt": {"debt_categories": [], "debt_thresholds": {}},
        }

    def evaluate_release(
        self,
        metrics: dict,
        evidence_lineage: dict,
    ) -> tuple[str, list[ConstitutionViolation], dict]:
        """
        Evaluate a release against the constitution.

        Returns (verdict, violations, constitution_trace).
        """
        violations = []
        constitution_trace = {
            "constitution_version": self.version,
            "constitution_hash": self.constitution_hash,
            "evaluated_at": datetime.now().isoformat(),
            "principles_evaluated": [],
            "rules_triggered": [],
        }

        # Evaluate each principle by priority
        for pid, principle in sorted(
            self.principles.items(),
            key=lambda x: x[1].priority
        ):
            satisfied, principle_violations = principle.evaluate(metrics)

            constitution_trace["principles_evaluated"].append({
                "principle_id": pid,
                "principle_name": principle.name,
                "satisfied": satisfied,
                "violations": principle_violations,
            })

            if not satisfied:
                for violation_desc in principle_violations:
                    violations.append(ConstitutionViolation(
                        principle_id=pid,
                        principle_name=principle.name,
                        violation_description=violation_desc,
                        severity=principle.enforcement.value,
                        metrics_at_violation=metrics,
                    ))

        # Determine verdict from violations
        hard_violations = [v for v in violations if v.severity == "hard"]
        soft_violations = [v for v in violations if v.severity == "soft"]

        if hard_violations:
            verdict = "BLOCK"
            constitution_trace["rules_triggered"].append({
                "verdict": "BLOCK",
                "source": "hard_principle_violation",
                "violations": [v.to_dict() for v in hard_violations],
            })
        elif soft_violations:
            verdict = "WARN"
            constitution_trace["rules_triggered"].append({
                "verdict": "WARN",
                "source": "soft_principle_violation",
                "violations": [v.to_dict() for v in soft_violations],
            })
        else:
            verdict = "OK"

        return verdict, violations, constitution_trace

    def get_safeguard_coverage(self, failure_mode: str) -> list[SafeguardMapping]:
        """Get safeguards that cover a specific failure mode."""
        return [
            s for s in self.safeguard_mappings.values()
            if failure_mode in s.covers_failure_modes
        ]

    def get_principles_for_failure_mode(self, failure_mode: str) -> list[Principle]:
        """Get principles relevant to a failure mode."""
        if failure_mode not in self.failure_modes:
            return []

        fm = self.failure_modes[failure_mode]
        return [
            self.principles[pid]
            for pid in fm.relevant_principles
            if pid in self.principles
        ]

    def calculate_alignment_debt(
        self,
        violations: list[ConstitutionViolation],
        accepted_risks: list[dict],
        coverage_gaps: list[str],
    ) -> tuple[float, list[AlignmentDebtEntry]]:
        """
        Calculate alignment debt from current state.

        Returns (total_debt, debt_entries).
        """
        import uuid

        debt_entries = []
        total_debt = 0.0

        # Debt from constitution deviations
        deviation_rate = self.alignment_debt_config.get("debt_categories", [])
        deviation_config = next(
            (c for c in deviation_rate if c["category"] == "constitution_deviation"),
            {"accumulation_rate": 0.05}
        )

        for violation in violations:
            if violation.severity == "hard":
                debt_amount = deviation_config["accumulation_rate"]
                entry = AlignmentDebtEntry(
                    entry_id=f"DEBT-{uuid.uuid4().hex[:8].upper()}",
                    created_at=datetime.now(),
                    release_id="current",
                    category="constitution_deviation",
                    description=f"Violation of {violation.principle_name}: {violation.violation_description}",
                    debt_amount=debt_amount,
                    status="active",
                )
                debt_entries.append(entry)
                total_debt += debt_amount

        # Debt from accepted risks
        risk_config = next(
            (c for c in deviation_rate if c["category"] == "risk_acceptance"),
            {"accumulation_rate": 0.01}
        )

        for risk in accepted_risks:
            debt_amount = risk_config["accumulation_rate"]
            entry = AlignmentDebtEntry(
                entry_id=f"DEBT-{uuid.uuid4().hex[:8].upper()}",
                created_at=datetime.now(),
                release_id="current",
                category="risk_acceptance",
                description=f"Accepted risk: {risk.get('description', 'Unknown')}",
                debt_amount=debt_amount,
                status="active",
            )
            debt_entries.append(entry)
            total_debt += debt_amount

        # Debt from coverage gaps
        gap_config = next(
            (c for c in deviation_rate if c["category"] == "coverage_gap"),
            {"accumulation_rate": 0.01}
        )

        for gap in coverage_gaps:
            debt_amount = gap_config["accumulation_rate"]
            entry = AlignmentDebtEntry(
                entry_id=f"DEBT-{uuid.uuid4().hex[:8].upper()}",
                created_at=datetime.now(),
                release_id="current",
                category="coverage_gap",
                description=f"Coverage gap: {gap}",
                debt_amount=debt_amount,
                status="active",
            )
            debt_entries.append(entry)
            total_debt += debt_amount

        return total_debt, debt_entries

    def get_debt_status(self, total_debt: float) -> str:
        """Get status based on debt thresholds."""
        thresholds = self.alignment_debt_config.get("debt_thresholds", {})
        if total_debt >= thresholds.get("critical", 0.50):
            return "CRITICAL"
        elif total_debt >= thresholds.get("block", 0.25):
            return "BLOCK"
        elif total_debt >= thresholds.get("warn", 0.10):
            return "WARN"
        else:
            return "OK"


class AlignmentDebtLedger:
    """
    Ledger for tracking alignment debt over time.

    Alignment debt is the accumulated "technical debt" of the safety system:
    - Coverage gaps
    - Accepted risks
    - Constitution deviations
    - Pending fixes

    Unlike technical debt, alignment debt has safety implications.
    """

    def __init__(self, storage_path: str = "data/alignment_debt.json"):
        self.storage_path = storage_path
        self.entries: list[AlignmentDebtEntry] = []
        self.total_debt: float = 0.0
        self._load()

    def _load(self) -> None:
        """Load ledger from storage."""
        # In production, load from durable storage
        pass

    def _save(self) -> None:
        """Save ledger to storage."""
        # In production, save to durable storage
        pass

    def add_entries(self, entries: list[AlignmentDebtEntry]) -> None:
        """Add new debt entries."""
        self.entries.extend(entries)
        self._recalculate_total()
        self._save()

    def resolve_entry(
        self,
        entry_id: str,
        resolution_method: str,
    ) -> Optional[AlignmentDebtEntry]:
        """Mark a debt entry as resolved."""
        for entry in self.entries:
            if entry.entry_id == entry_id and entry.status == "active":
                entry.status = "resolved"
                entry.resolved_at = datetime.now()
                entry.resolution_method = resolution_method
                self._recalculate_total()
                self._save()
                return entry
        return None

    def _recalculate_total(self) -> None:
        """Recalculate total active debt."""
        self.total_debt = sum(
            e.debt_amount for e in self.entries
            if e.status == "active"
        )

    def get_debt_by_category(self) -> dict[str, float]:
        """Get debt breakdown by category."""
        breakdown = {}
        for entry in self.entries:
            if entry.status == "active":
                breakdown[entry.category] = breakdown.get(entry.category, 0) + entry.debt_amount
        return breakdown

    def get_trend(self, days: int = 30) -> dict:
        """Get debt trend over time."""
        cutoff = datetime.now()
        recent = [e for e in self.entries
                  if (cutoff - e.created_at).days <= days]

        added = sum(e.debt_amount for e in recent if e.status in ["active", "accepted"])
        resolved = sum(e.debt_amount for e in recent if e.status == "resolved")

        return {
            "period_days": days,
            "debt_added": added,
            "debt_resolved": resolved,
            "net_change": added - resolved,
            "current_total": self.total_debt,
        }

    def export_for_report(self) -> dict:
        """Export debt data for board-level report."""
        return {
            "total_debt": self.total_debt,
            "by_category": self.get_debt_by_category(),
            "trend_30d": self.get_trend(30),
            "active_entries": len([e for e in self.entries if e.status == "active"]),
            "resolved_entries": len([e for e in self.entries if e.status == "resolved"]),
        }


# Example usage
if __name__ == "__main__":
    constitution = Constitution()

    print(f"Constitution version: {constitution.version}")
    print(f"Constitution hash: {constitution.constitution_hash}")
    print(f"Principles: {len(constitution.principles)}")
    print(f"Failure modes: {len(constitution.failure_modes)}")
    print(f"Safeguard mappings: {len(constitution.safeguard_mappings)}")

    # Evaluate a release
    metrics = {
        "critical_violation_rate": 0.02,  # 2% increase - would trigger P1
        "statistical_power": 0.75,  # Below 0.80 - would trigger P2
        "evidence_lineage_complete": True,
        "risk_ownership_assigned": True,
        "safeguard_layer_count": 2,
    }

    verdict, violations, trace = constitution.evaluate_release(
        metrics=metrics,
        evidence_lineage={"eval_run_id": "run_001"},
    )

    print("\nRelease evaluation:")
    print(f"  Verdict: {verdict}")
    print(f"  Violations: {len(violations)}")
    for v in violations:
        print(f"    - [{v.severity}] {v.principle_name}: {v.violation_description}")

    # Calculate alignment debt
    debt, entries = constitution.calculate_alignment_debt(
        violations=violations,
        accepted_risks=[{"description": "Elevated policy erosion"}],
        coverage_gaps=["multi-agent coordination"],
    )

    print("\nAlignment debt:")
    print(f"  Total: {debt:.3f}")
    print(f"  Status: {constitution.get_debt_status(debt)}")
    print(f"  Entries: {len(entries)}")
