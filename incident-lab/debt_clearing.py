"""
Alignment Debt Clearing Module

Automatically clears alignment debt entries when incidents are resolved
through successful regression test promotion and verification.

Workflow:
1. Incident occurs → Debt entry created (status: open)
2. Incident analyzed → RCA completed, regression test generated
3. Regression test promoted → Passes in CI
4. Debt cleared → Status: open → mitigated

This closes the loop: every safety failure becomes institutional knowledge,
and debt is only cleared when mitigations are verified working.

Usage:
    from debt_clearing import DebtClearer
    clearer = DebtClearer()
    clearer.mark_mitigated("INC_004", evidence=["REG-CM-001"])
"""

import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, field


@dataclass
class DebtEntry:
    """Structured alignment debt entry."""
    debt_id: str
    status: str  # open, mitigated, accepted, expired
    principle: str
    mechanism_gap: str
    introduced_by_release: str
    severity: str
    blocks_release: bool
    mitigation_status: str  # open, in_progress, mitigated
    evidence: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    mitigated_at: Optional[str] = None
    mitigated_by: Optional[str] = None
    regression_tests: List[str] = field(default_factory=list)


class DebtClearer:
    """
    Manages alignment debt lifecycle.

    Connects incident resolution to debt clearing through verified mitigations.
    """

    def __init__(
        self,
        debt_path: Optional[Path] = None,
        regression_suite_root: Optional[Path] = None
    ):
        self.root = Path(__file__).resolve().parent

        # Default paths
        if debt_path is None:
            # Try model-safety-regression-suite first, fall back to local
            suite_path = self.root.parent / "model-safety-regression-suite" / "artifacts" / "alignment_debt.yaml"
            local_path = self.root / "artifacts" / "alignment_debt.yaml"
            self.debt_path = suite_path if suite_path.exists() else local_path
        else:
            self.debt_path = debt_path

        if regression_suite_root is None:
            self.regression_suite_root = self.root.parent / "model-safety-regression-suite"
        else:
            self.regression_suite_root = regression_suite_root

    def load_debt_ledger(self) -> Dict:
        """Load alignment debt ledger from YAML."""
        if not self.debt_path.exists():
            return {
                "run_id": "unknown",
                "generated_at": datetime.utcnow().isoformat() + "Z",
                "summary": {"total_active_debt": 0.0, "debt_status": "OK"},
                "ledger": []
            }

        with open(self.debt_path, "r") as f:
            return yaml.safe_load(f)

    def save_debt_ledger(self, ledger: Dict) -> None:
        """Save updated alignment debt ledger."""
        self.debt_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.debt_path, "w") as f:
            yaml.safe_dump(ledger, f, default_flow_style=False, sort_keys=False)

    def find_debt_by_incident(self, incident_id: str) -> Optional[Dict]:
        """Find debt entry associated with an incident."""
        ledger = self.load_debt_ledger()
        for entry in ledger.get("ledger", []):
            # Match by incident ID in evidence
            evidence = entry.get("evidence", {})
            if isinstance(evidence, dict):
                regression_tests = evidence.get("regression_tests", [])
            elif isinstance(evidence, list):
                regression_tests = evidence
            else:
                regression_tests = []

            # Check if incident ID appears in evidence
            for test_id in regression_tests:
                if incident_id in test_id:
                    return entry

            # Also check debt_id pattern
            if incident_id in entry.get("debt_id", ""):
                return entry

        return None

    def find_debt_by_principle(self, principle: str) -> List[Dict]:
        """Find all debt entries for a constitutional principle."""
        ledger = self.load_debt_ledger()
        return [
            entry for entry in ledger.get("ledger", [])
            if entry.get("principle") == principle
        ]

    def mark_mitigated(
        self,
        incident_id: str,
        evidence: List[str],
        mitigated_by: str = "regression_promotion"
    ) -> Dict:
        """
        Mark debt as mitigated after successful regression test promotion.

        Args:
            incident_id: The incident that triggered the debt
            evidence: List of regression test IDs that verify the mitigation
            mitigated_by: How the mitigation was verified

        Returns:
            Updated debt entry
        """
        ledger = self.load_debt_ledger()
        timestamp = datetime.utcnow().isoformat() + "Z"

        updated_entry = None
        for entry in ledger.get("ledger", []):
            # Match by incident ID patterns
            debt_id = entry.get("debt_id", "")
            entry_evidence = entry.get("evidence", {})

            # Check various matching patterns
            match = False
            if incident_id in debt_id:
                match = True
            elif isinstance(entry_evidence, dict):
                if incident_id in str(entry_evidence.get("regression_tests", [])):
                    match = True
            elif isinstance(entry_evidence, list):
                if incident_id in str(entry_evidence):
                    match = True

            if match and entry.get("mitigation_status") != "mitigated":
                entry["mitigation_status"] = "mitigated"
                entry["mitigated_at"] = timestamp
                entry["mitigated_by"] = mitigated_by
                entry["blocks_release"] = False

                # Add new regression tests to evidence
                if isinstance(entry.get("evidence"), dict):
                    existing = entry["evidence"].get("regression_tests", [])
                    entry["evidence"]["regression_tests"] = list(set(existing + evidence))
                    entry["evidence"]["mitigation_verified_at"] = timestamp
                elif isinstance(entry.get("evidence"), list):
                    entry["evidence"] = {
                        "regression_tests": list(set(entry["evidence"] + evidence)),
                        "mitigation_verified_at": timestamp
                    }

                updated_entry = entry
                break

        if updated_entry:
            # Recalculate summary
            self._recalculate_summary(ledger)
            self.save_debt_ledger(ledger)

        return updated_entry or {}

    def mark_accepted(
        self,
        debt_id: str,
        approved_by: str,
        expires: str,
        conditions: List[str]
    ) -> Dict:
        """
        Mark debt as accepted with explicit risk acknowledgment.

        Used when a fix is not immediately possible but risk is understood.

        Args:
            debt_id: The debt entry ID
            approved_by: Who approved the risk acceptance
            expires: Expiration date for the acceptance
            conditions: Conditions under which acceptance is valid

        Returns:
            Updated debt entry
        """
        ledger = self.load_debt_ledger()
        timestamp = datetime.utcnow().isoformat() + "Z"

        updated_entry = None
        for entry in ledger.get("ledger", []):
            if entry.get("debt_id") == debt_id:
                entry["mitigation_status"] = "accepted"
                entry["blocks_release"] = False  # No longer blocks if accepted
                entry["risk_acceptance"] = {
                    "approved_by": approved_by,
                    "approved_at": timestamp,
                    "expires": expires,
                    "conditions": conditions
                }
                updated_entry = entry
                break

        if updated_entry:
            self._recalculate_summary(ledger)
            self.save_debt_ledger(ledger)

        return updated_entry or {}

    def create_debt_from_incident(
        self,
        incident_id: str,
        principle: str,
        mechanism_gap: str,
        severity: str,
        release_id: str,
        evidence: List[str]
    ) -> Dict:
        """
        Create new debt entry from an incident.

        Called when an incident analysis identifies a gap that needs tracking.

        Args:
            incident_id: The incident ID
            principle: Constitutional principle violated (C1-C6)
            mechanism_gap: Description of the safeguard gap
            severity: critical, high, medium
            release_id: Release that introduced/exposed the gap
            evidence: List of test/incident IDs as evidence

        Returns:
            Created debt entry
        """
        ledger = self.load_debt_ledger()
        timestamp = datetime.utcnow().isoformat() + "Z"

        debt_id = f"AD-{datetime.utcnow().strftime('%Y%m%d')}-{incident_id}"

        new_entry = {
            "debt_id": debt_id,
            "status": "active",
            "created_at": timestamp,
            "introduced_by_release": release_id,
            "principle": principle,
            "violation_type": "incident_derived",
            "mechanism_gap": mechanism_gap,
            "description": f"Gap identified from incident {incident_id}",
            "severity": severity,
            "debt_amount": {"critical": 0.10, "high": 0.05, "medium": 0.02}.get(severity, 0.02),
            "blocks_release": severity in ("critical", "high"),
            "evidence": {
                "source_incident": incident_id,
                "regression_tests": evidence
            },
            "mitigation_status": "open",
            "planned_resolution": {
                "owner": "Safety Engineering",
                "eta": "TBD"
            }
        }

        ledger.setdefault("ledger", []).append(new_entry)
        self._recalculate_summary(ledger)
        self.save_debt_ledger(ledger)

        return new_entry

    def _recalculate_summary(self, ledger: Dict) -> None:
        """Recalculate summary statistics after debt changes."""
        entries = ledger.get("ledger", [])

        # Only count non-mitigated, non-accepted debt
        active_entries = [
            e for e in entries
            if e.get("mitigation_status") not in ("mitigated", "accepted")
        ]

        total_debt = sum(
            e.get("debt_amount", 0.05) if isinstance(e.get("debt_amount"), (int, float))
            else 0.05
            for e in active_entries
        )

        # Determine status
        if total_debt >= 0.25:
            status = "BLOCK"
        elif total_debt >= 0.10:
            status = "WARN"
        else:
            status = "OK"

        ledger["summary"] = {
            "total_active_debt": round(total_debt, 3),
            "debt_status": status,
            "active_entries": len(active_entries),
            "mitigated_entries": len([e for e in entries if e.get("mitigation_status") == "mitigated"]),
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    def get_blocking_debt(self) -> List[Dict]:
        """Get all debt entries that block release."""
        ledger = self.load_debt_ledger()
        return [
            entry for entry in ledger.get("ledger", [])
            if entry.get("blocks_release", False)
            and entry.get("mitigation_status") not in ("mitigated", "accepted")
        ]

    def generate_debt_report(self) -> str:
        """Generate human-readable debt report."""
        ledger = self.load_debt_ledger()
        summary = ledger.get("summary", {})
        ledger.get("ledger", [])

        report = []
        report.append("=" * 60)
        report.append("ALIGNMENT DEBT REPORT")
        report.append("=" * 60)
        report.append("")
        report.append(f"Status: {summary.get('debt_status', 'UNKNOWN')}")
        report.append(f"Total Active Debt: {summary.get('total_active_debt', 0):.3f}")
        report.append(f"Active Entries: {summary.get('active_entries', 0)}")
        report.append(f"Mitigated Entries: {summary.get('mitigated_entries', 0)}")
        report.append("")

        blocking = self.get_blocking_debt()
        if blocking:
            report.append("BLOCKING DEBT:")
            for entry in blocking:
                report.append(f"  - {entry.get('debt_id')}: {entry.get('mechanism_gap', 'Unknown')}")
                report.append(f"    Principle: {entry.get('principle')} | Severity: {entry.get('severity')}")
            report.append("")

        report.append("=" * 60)
        return "\n".join(report)


def clear_debt_for_incident(incident_id: str, regression_tests: List[str]) -> Dict:
    """
    Convenience function to clear debt when an incident is resolved.

    Call this after promoting an incident to the regression suite
    and verifying the regression tests pass.

    Args:
        incident_id: The incident ID (e.g., "INC_004")
        regression_tests: List of regression test IDs that verify the fix

    Returns:
        Updated debt entry or empty dict if not found
    """
    clearer = DebtClearer()
    return clearer.mark_mitigated(incident_id, regression_tests)


if __name__ == "__main__":
    # Demo usage
    import argparse

    parser = argparse.ArgumentParser(description="Alignment Debt Management")
    parser.add_argument("--report", action="store_true", help="Generate debt report")
    parser.add_argument("--mitigate", type=str, help="Mark incident as mitigated")
    parser.add_argument("--evidence", type=str, nargs="+", default=[], help="Evidence test IDs")
    parser.add_argument("--blocking", action="store_true", help="Show blocking debt")
    args = parser.parse_args()

    clearer = DebtClearer()

    if args.report:
        print(clearer.generate_debt_report())
    elif args.mitigate:
        result = clearer.mark_mitigated(args.mitigate, args.evidence)
        if result:
            print(f"[OK] Marked {args.mitigate} as mitigated")
            print(f"     Debt ID: {result.get('debt_id')}")
        else:
            print(f"[WARN] No matching debt found for {args.mitigate}")
    elif args.blocking:
        blocking = clearer.get_blocking_debt()
        if blocking:
            print("Blocking debt entries:")
            for entry in blocking:
                print(f"  - {entry.get('debt_id')}: {entry.get('mechanism_gap')}")
        else:
            print("No blocking debt entries")
    else:
        parser.print_help()
