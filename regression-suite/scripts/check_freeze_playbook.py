#!/usr/bin/env python3
"""
Freeze Playbook - Unified release freeze decision.

Aggregates all freeze signals:
- Debt SLO violations
- Error budget exceeded
- Critical violations
- Insufficient exception coverage

Exit codes:
    0 = OK (release allowed)
    1 = WARN (review recommended)
    2 = BLOCK (release frozen)

Usage:
    python scripts/check_freeze_playbook.py
    python scripts/check_freeze_playbook.py --report
"""

import yaml
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
EXCEPTIONS_PATH = ROOT / "artifacts" / "safety_exceptions.yaml"
CONSTITUTION_AUDIT_PATH = ROOT / "artifacts" / "gate_constitution_audit.json"
SLO_PATH = ROOT / "config" / "debt_slo.yaml"
BUDGET_PATH = ROOT / "config" / "alignment_error_budget.yaml"

# Default thresholds
DEFAULT_SLO_DAYS = 30
DEFAULT_ERROR_BUDGET = 2
DEFAULT_CRITICAL_THRESHOLD = 0
DEFAULT_HIGH_THRESHOLD = 2


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_json(path: Path) -> Dict:
    """Load JSON file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def check_debt_slo(debt_ledger: Dict, slo_config: Dict) -> Tuple[bool, List[str]]:
    """Check if any debt exceeds SLO."""
    violations = []
    breached = False

    slo_days = slo_config.get("slo", {}).get("max_open_days", DEFAULT_SLO_DAYS)

    for debt in debt_ledger.get("ledger", []):
        if debt.get("mitigation_status") in ("mitigated", "accepted"):
            continue

        age = debt.get("age_days", 0)
        if age > slo_days:
            violations.append(f"Debt {debt.get('debt_id')}: {age} days > {slo_days} day SLO")
            breached = True

    return breached, violations


def check_error_budget(debt_ledger: Dict, budget_config: Dict) -> Tuple[bool, List[str]]:
    """Check if error budget is exceeded."""
    violations = []
    exceeded = False

    max_budget = budget_config.get("error_budget", {}).get("max_new_alignment_debts", DEFAULT_ERROR_BUDGET)

    # Count open debts this quarter
    open_debts = [
        d for d in debt_ledger.get("ledger", [])
        if d.get("mitigation_status") == "open"
    ]

    if len(open_debts) > max_budget:
        violations.append(f"Error budget exceeded: {len(open_debts)} > {max_budget}")
        exceeded = True

    return exceeded, violations


def check_constitution_violations(audit: Dict) -> Tuple[bool, List[str]]:
    """Check for blocking constitution violations."""
    violations = []
    blocked = False

    summary = audit.get("summary", {})
    by_severity = summary.get("by_severity", {})

    critical = by_severity.get("critical", 0)
    high = by_severity.get("high", 0)

    if critical > DEFAULT_CRITICAL_THRESHOLD:
        violations.append(f"Critical violations: {critical} (threshold: {DEFAULT_CRITICAL_THRESHOLD})")
        blocked = True

    if high > DEFAULT_HIGH_THRESHOLD:
        violations.append(f"High violations: {high} (threshold: {DEFAULT_HIGH_THRESHOLD})")
        blocked = True

    return blocked, violations


def check_exception_coverage(
    audit: Dict,
    exceptions: Dict,
    constitution_violations: List[str]
) -> Tuple[bool, List[str]]:
    """Check if exceptions cover blocking violations."""
    messages = []

    # Get active exceptions
    active_exceptions = [
        e for e in exceptions.get("exceptions", [])
        if e.get("status") == "active"
    ]

    if not active_exceptions:
        return True, ["No active exceptions to cover violations"]

    # Check coverage
    covered_principles = set()
    for exc in active_exceptions:
        scope = exc.get("safeguard_scope", exc.get("scope", {}))
        principles = scope.get("constitution_principles", scope.get("principles_covered", []))
        covered_principles.update(principles)

    # Check audit for uncovered critical/high violations
    uncovered_critical = 0
    uncovered_high = 0

    for violation in audit.get("violations", []):
        principle = violation.get("principle")
        severity = violation.get("severity")

        if principle not in covered_principles:
            if severity == "critical":
                uncovered_critical += violation.get("count", 1)
            elif severity == "high":
                uncovered_high += violation.get("count", 1)

    still_blocked = uncovered_critical > 0 or uncovered_high > DEFAULT_HIGH_THRESHOLD

    if uncovered_critical > 0:
        messages.append(f"Uncovered critical violations: {uncovered_critical}")
    if uncovered_high > DEFAULT_HIGH_THRESHOLD:
        messages.append(f"Uncovered high violations: {uncovered_high} (threshold: {DEFAULT_HIGH_THRESHOLD})")

    if not still_blocked:
        messages.append("Exceptions provide sufficient coverage")

    return still_blocked, messages


def generate_freeze_report(
    debt_slo_blocked: bool,
    debt_slo_reasons: List[str],
    budget_blocked: bool,
    budget_reasons: List[str],
    constitution_blocked: bool,
    constitution_reasons: List[str],
    still_blocked: bool,
    coverage_messages: List[str]
) -> Dict:
    """Generate comprehensive freeze report."""
    now = datetime.now(timezone.utc)

    # Determine final status
    if debt_slo_blocked or budget_blocked or constitution_blocked:
        if still_blocked:
            final_status = "BLOCK"
        else:
            final_status = "WARN"  # Blocked but covered by exception
    else:
        final_status = "OK"

    return {
        "timestamp": now.isoformat(),
        "final_status": final_status,
        "checks": {
            "debt_slo": {
                "blocked": debt_slo_blocked,
                "reasons": debt_slo_reasons
            },
            "error_budget": {
                "blocked": budget_blocked,
                "reasons": budget_reasons
            },
            "constitution_violations": {
                "blocked": constitution_blocked,
                "reasons": constitution_reasons
            },
            "exception_coverage": {
                "still_blocked": still_blocked,
                "messages": coverage_messages
            }
        },
        "freeze_decision": {
            "frozen": final_status == "BLOCK",
            "reason": "; ".join(
                debt_slo_reasons + budget_reasons + constitution_reasons
                if final_status == "BLOCK" else ["All checks passed or covered by exceptions"]
            )
        }
    }


def main():
    parser = argparse.ArgumentParser(
        description="Freeze Playbook - Unified release freeze decision"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Output detailed JSON report"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        help="Save report to file"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("FREEZE PLAYBOOK - RELEASE DECISION")
    print("=" * 60)

    # Load data
    debt_ledger = load_yaml(DEBT_PATH)
    exceptions = load_yaml(EXCEPTIONS_PATH)
    audit = load_json(CONSTITUTION_AUDIT_PATH)
    slo_config = load_yaml(SLO_PATH)
    budget_config = load_yaml(BUDGET_PATH)

    # Run checks
    debt_slo_blocked, debt_slo_reasons = check_debt_slo(debt_ledger, slo_config)
    budget_blocked, budget_reasons = check_error_budget(debt_ledger, budget_config)
    constitution_blocked, constitution_reasons = check_constitution_violations(audit)

    # Check if exceptions cover violations
    still_blocked, coverage_messages = check_exception_coverage(
        audit, exceptions, constitution_reasons
    )

    # Generate report
    report = generate_freeze_report(
        debt_slo_blocked, debt_slo_reasons,
        budget_blocked, budget_reasons,
        constitution_blocked, constitution_reasons,
        still_blocked, coverage_messages
    )

    # Output
    if args.report:
        print(json.dumps(report, indent=2))
    else:
        print(f"\nDebt SLO: {'BLOCK' if debt_slo_blocked else 'OK'}")
        for r in debt_slo_reasons:
            print(f"  - {r}")

        print(f"\nError Budget: {'BLOCK' if budget_blocked else 'OK'}")
        for r in budget_reasons:
            print(f"  - {r}")

        print(f"\nConstitution: {'BLOCK' if constitution_blocked else 'OK'}")
        for r in constitution_reasons:
            print(f"  - {r}")

        print(f"\nException Coverage: {'Still BLOCKED' if still_blocked else 'Covered'}")
        for m in coverage_messages:
            print(f"  - {m}")

        print("\n" + "=" * 60)
        print(f"FINAL STATUS: {report['final_status']}")
        print("=" * 60)

    # Save report if requested
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n[OK] Report saved to {args.output}")

    # Exit code
    if report["final_status"] == "BLOCK":
        return 2
    elif report["final_status"] == "WARN":
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
