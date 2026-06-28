#!/usr/bin/env python3
"""
Exception Blast Radius Limiter

Hard constraints enforced:
- Exception must not cross repo boundaries
- Exception scope must be limited to declared safeguards / constitution principles
- Renewal count must not exceed max_renewals
- Incident review must be scheduled for active exceptions
- Exception entropy (coverage breadth) must not exceed threshold

This prevents safety governance from becoming a blanket override mechanism.

Exit codes:
    0 = All exceptions within blast radius limits
    1 = Warning (approaching limits)
    2 = BLOCK: Blast radius violations detected

Usage:
    python scripts/check_exception_blast_radius.py
    python scripts/check_exception_blast_radius.py --strict
"""

import yaml
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

EXCEPTIONS_PATH = ROOT / "artifacts" / "safety_exceptions.yaml"
CONSTITUTION_PATH = ROOT / "config" / "constitution_v2.yaml"
THIS_REPO = "model-safety-regression-suite"

# Entropy budget: max safeguards + principles an exception can cover
MAX_SAFEGUARD_COVERAGE = 5
MAX_PRINCIPLE_COVERAGE = 3
MAX_ENTROPY_SCORE = 10  # Combined weighted score


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def calculate_entropy_score(exception: Dict) -> float:
    """
    Calculate exception entropy score.

    Higher entropy = broader coverage = higher risk of abuse.
    """
    scope = exception.get("safeguard_scope", exception.get("scope", {}))

    safeguards = scope.get("safeguards", scope.get("safeguards_affected", []))
    principles = scope.get("constitution_principles", scope.get("principles_covered", []))

    # Weight: principles are more impactful than individual safeguards
    safeguard_score = len(safeguards) * 1.0
    principle_score = len(principles) * 2.0

    return safeguard_score + principle_score


def validate_blast_radius(exception: Dict) -> List[str]:
    """
    Validate a single exception's blast radius.

    Returns list of violations (empty if valid).
    """
    violations = []
    exception_id = exception.get("exception_id", "unknown")

    # Skip inactive exceptions
    if exception.get("status") not in (None, "active"):
        return []

    # 1. Check repo scope (no cross-repo exceptions)
    repo_scope = exception.get("repo_scope")
    if repo_scope and repo_scope != THIS_REPO:
        violations.append(f"{exception_id}: cross-repo exception forbidden (scope: {repo_scope})")

    # 2. Check renewal count
    renewal_count = exception.get("renewal_count", exception.get("renewals", {}).get("count", 0))
    max_renewals = exception.get("max_renewals", exception.get("renewals", {}).get("max_allowed", 2))
    if renewal_count > max_renewals:
        violations.append(f"{exception_id}: renewal count exceeded ({renewal_count} > {max_renewals})")

    # 3. Check incident review scheduling
    ir = exception.get("incident_review", {})
    if ir.get("required") and not ir.get("scheduled_for") and not ir.get("meeting_id"):
        violations.append(f"{exception_id}: incident review required but not scheduled")

    # 4. Check scope is not empty (must specify blast radius)
    scope = exception.get("safeguard_scope", exception.get("scope", {}))
    safeguards = scope.get("safeguards", scope.get("safeguards_affected", []))
    principles = scope.get("constitution_principles", scope.get("principles_covered", []))

    if not safeguards and not principles:
        violations.append(f"{exception_id}: empty blast radius (must specify safeguards or principles)")

    # 5. Check entropy budget
    entropy = calculate_entropy_score(exception)
    if entropy > MAX_ENTROPY_SCORE:
        violations.append(f"{exception_id}: entropy score {entropy} exceeds budget {MAX_ENTROPY_SCORE}")

    # 6. Check safeguard coverage limit
    if len(safeguards) > MAX_SAFEGUARD_COVERAGE:
        violations.append(f"{exception_id}: too many safeguards ({len(safeguards)} > {MAX_SAFEGUARD_COVERAGE})")

    # 7. Check principle coverage limit
    if len(principles) > MAX_PRINCIPLE_COVERAGE:
        violations.append(f"{exception_id}: too many principles ({len(principles)} > {MAX_PRINCIPLE_COVERAGE})")

    return violations


def validate_all_exceptions(exceptions_config: Dict) -> Tuple[List[Dict], List[str]]:
    """
    Validate all exceptions' blast radius.

    Returns (valid_exceptions, all_violations).
    """
    all_violations = []
    valid_exceptions = []

    for exception in exceptions_config.get("exceptions", []):
        violations = validate_blast_radius(exception)

        if violations:
            all_violations.extend(violations)
        else:
            if exception.get("status") in (None, "active"):
                valid_exceptions.append(exception)

    return valid_exceptions, all_violations


def generate_audit_report(
    valid_exceptions: List[Dict],
    violations: List[str]
) -> Dict:
    """Generate audit report for gate_report.html integration."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "valid_count": len(valid_exceptions),
        "violation_count": len(violations),
        "violations": violations,
        "valid_exceptions": [
            {
                "exception_id": e.get("exception_id"),
                "repo_scope": e.get("repo_scope", THIS_REPO),
                "safeguard_scope": e.get("safeguard_scope", e.get("scope", {})),
                "renewal_count": e.get("renewal_count", e.get("renewals", {}).get("count", 0)),
                "max_renewals": e.get("max_renewals", e.get("renewals", {}).get("max_allowed", 2)),
                "entropy_score": calculate_entropy_score(e),
                "incident_review": e.get("incident_review", {})
            }
            for e in valid_exceptions
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description="Validate exception blast radius limits"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Treat warnings as errors"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--report",
        type=Path,
        help="Save audit report to file"
    )
    args = parser.parse_args()

    exceptions_config = load_yaml(EXCEPTIONS_PATH)
    valid_exceptions, violations = validate_all_exceptions(exceptions_config)

    audit_report = generate_audit_report(valid_exceptions, violations)

    if args.json:
        print(json.dumps(audit_report, indent=2, default=str))
    else:
        print("=" * 60)
        print("EXCEPTION BLAST RADIUS VALIDATION")
        print("=" * 60)

        if valid_exceptions:
            print(f"\n[OK] Valid exceptions: {len(valid_exceptions)}")
            for e in valid_exceptions:
                eid = e.get("exception_id")
                entropy = calculate_entropy_score(e)
                renewal = e.get("renewal_count", e.get("renewals", {}).get("count", 0))
                max_r = e.get("max_renewals", e.get("renewals", {}).get("max_allowed", 2))
                print(f"  - {eid}")
                print(f"    Entropy: {entropy}/{MAX_ENTROPY_SCORE} | Renewals: {renewal}/{max_r}")

        if violations:
            print(f"\n[BLOCK] Blast radius violations: {len(violations)}")
            for v in violations:
                print(f"  - {v}")

        print("\n" + "=" * 60)

    # Save report if requested
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        with open(args.report, "w") as f:
            json.dump(audit_report, f, indent=2, default=str)
        print(f"\n[OK] Report saved to {args.report}")

    # Determine exit code
    if violations:
        print("\n[GATE] BLOCK: Exception blast radius violations detected")
        return 2

    # Check for warnings (approaching limits)
    warnings = []
    for e in valid_exceptions:
        entropy = calculate_entropy_score(e)
        if entropy > MAX_ENTROPY_SCORE * 0.8:
            warnings.append(f"{e.get('exception_id')}: entropy {entropy} approaching limit")

        renewal = e.get("renewal_count", e.get("renewals", {}).get("count", 0))
        max_r = e.get("max_renewals", e.get("renewals", {}).get("max_allowed", 2))
        if renewal >= max_r:
            warnings.append(f"{e.get('exception_id')}: at max renewals ({renewal}/{max_r})")

    if warnings:
        print(f"\n[WARN] {len(warnings)} exception(s) approaching limits")
        for w in warnings:
            print(f"  - {w}")
        if args.strict:
            return 1

    print("\n[GATE] Exception blast radius validated")
    return 0


if __name__ == "__main__":
    sys.exit(main())
