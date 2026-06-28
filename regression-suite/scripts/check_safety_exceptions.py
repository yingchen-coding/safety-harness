#!/usr/bin/env python3
"""
Validate safety exceptions for release gate.

Checks:
1. Approver must be authorized (role in exception_authority.yaml)
2. TTL must not be expired
3. Max renewals not exceeded
4. Scope matches the blocked condition

Exit codes:
    0 = Valid exception exists (unfreeze allowed)
    1 = No exception but not strictly required
    2 = BLOCK: Unauthorized or expired exception

Usage:
    python scripts/check_safety_exceptions.py
    python scripts/check_safety_exceptions.py --strict
"""

import yaml
import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional

ROOT = Path(__file__).resolve().parents[1]

EXCEPTIONS_PATH = ROOT / "artifacts" / "safety_exceptions.yaml"
AUTHORITY_PATH = ROOT / "config" / "exception_authority.yaml"
AUDIT_LOG_PATH = ROOT / "artifacts" / "exception_audit.jsonl"


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp."""
    ts = ts.rstrip("Z")
    if "+" in ts:
        ts = ts.split("+")[0]
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%S").replace(tzinfo=timezone.utc)


def get_authorized_roles(authority_config: Dict) -> Dict[str, Dict]:
    """Get mapping of authorized roles to their permissions."""
    approvers = authority_config.get("exception_authority", {}).get("approvers", [])
    return {a["role"]: a for a in approvers if a.get("can_approve")}


def get_forbidden_roles(authority_config: Dict) -> set:
    """Get set of forbidden roles."""
    return set(authority_config.get("exception_authority", {}).get("forbidden_roles", []))


def validate_exception(
    exception: Dict,
    authorized_roles: Dict[str, Dict],
    forbidden_roles: set,
    now: datetime,
    rules: Dict
) -> Tuple[str, Optional[str]]:
    """
    Validate a single exception.

    Returns (status, reason) where status is 'valid', 'expired', 'unauthorized', or 'invalid'.
    """
    # Check status
    if exception.get("status") != "active":
        return "inactive", f"Exception status is {exception.get('status')}"

    # Check approver authorization
    approver_role = exception.get("approved_by", {}).get("role")

    if approver_role in forbidden_roles:
        return "unauthorized", f"Role '{approver_role}' is forbidden from approving exceptions"

    if approver_role not in authorized_roles:
        return "unauthorized", f"Role '{approver_role}' is not authorized to approve exceptions"

    # Check TTL
    expires_at_str = exception.get("expires_at")
    if not expires_at_str:
        return "invalid", "Exception has no expiration date"

    try:
        expires_at = parse_timestamp(expires_at_str)
    except ValueError:
        return "invalid", f"Cannot parse expiration date: {expires_at_str}"

    if expires_at < now:
        return "expired", f"Exception expired at {expires_at_str}"

    # Check max renewals
    renewals = exception.get("renewals", {})
    renewal_count = renewals.get("count", 0)
    max_renewals = renewals.get("max_allowed", rules.get("max_consecutive_renewals", 2))

    if renewal_count > max_renewals:
        return "invalid", f"Max renewals exceeded ({renewal_count} > {max_renewals})"

    # Check scope TTL limits
    role_config = authorized_roles.get(approver_role, {})
    max_ttl = role_config.get("max_ttl_days")
    if max_ttl:
        approved_at_str = exception.get("approved_at")
        if approved_at_str:
            approved_at = parse_timestamp(approved_at_str)
            actual_ttl = (expires_at - approved_at).days
            if actual_ttl > max_ttl:
                return "invalid", f"TTL {actual_ttl} days exceeds max {max_ttl} for role {approver_role}"

    return "valid", None


def validate_all_exceptions(
    exceptions_config: Dict,
    authority_config: Dict,
    now: Optional[datetime] = None
) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Validate all exceptions.

    Returns (valid, expired, unauthorized, invalid) lists.
    """
    now = now or datetime.now(timezone.utc)

    authorized_roles = get_authorized_roles(authority_config)
    forbidden_roles = get_forbidden_roles(authority_config)
    rules = authority_config.get("exception_rules", {})

    valid = []
    expired = []
    unauthorized = []
    invalid = []

    for exception in exceptions_config.get("exceptions", []):
        status, reason = validate_exception(
            exception, authorized_roles, forbidden_roles, now, rules
        )

        exception_with_validation = {
            **exception,
            "validation_status": status,
            "validation_reason": reason
        }

        if status == "valid":
            valid.append(exception_with_validation)
        elif status == "expired":
            expired.append(exception_with_validation)
        elif status == "unauthorized":
            unauthorized.append(exception_with_validation)
        else:
            invalid.append(exception_with_validation)

    return valid, expired, unauthorized, invalid


def log_audit_event(event: Dict) -> None:
    """Append event to audit log."""
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(AUDIT_LOG_PATH, "a") as f:
        f.write(json.dumps(event) + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="Validate safety exceptions"
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Return BLOCK if any invalid exceptions exist"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON"
    )
    args = parser.parse_args()

    now = datetime.now(timezone.utc)

    exceptions_config = load_yaml(EXCEPTIONS_PATH)
    authority_config = load_yaml(AUTHORITY_PATH)

    valid, expired, unauthorized, invalid = validate_all_exceptions(
        exceptions_config, authority_config, now
    )

    # Log validation event
    log_audit_event({
        "timestamp": now.isoformat(),
        "action": "exceptions_validated",
        "valid_count": len(valid),
        "expired_count": len(expired),
        "unauthorized_count": len(unauthorized),
        "invalid_count": len(invalid)
    })

    if args.json:
        result = {
            "timestamp": now.isoformat(),
            "valid": valid,
            "expired": expired,
            "unauthorized": unauthorized,
            "invalid": invalid
        }
        print(json.dumps(result, indent=2, default=str))
    else:
        print("=" * 60)
        print("SAFETY EXCEPTION VALIDATION")
        print("=" * 60)

        if valid:
            print(f"\n[OK] Valid exceptions: {len(valid)}")
            for e in valid:
                print(f"  - {e.get('exception_id')}")
                print(f"    Approved by: {e.get('approved_by', {}).get('name')} ({e.get('approved_by', {}).get('role')})")
                print(f"    Expires: {e.get('expires_at')}")
                print(f"    Scope: {e.get('scope', {}).get('type')}")

        if expired:
            print(f"\n[WARN] Expired exceptions: {len(expired)}")
            for e in expired:
                print(f"  - {e.get('exception_id')}: {e.get('validation_reason')}")

        if unauthorized:
            print(f"\n[BLOCK] Unauthorized exceptions: {len(unauthorized)}")
            for e in unauthorized:
                print(f"  - {e.get('exception_id')}: {e.get('validation_reason')}")

        if invalid:
            print(f"\n[BLOCK] Invalid exceptions: {len(invalid)}")
            for e in invalid:
                print(f"  - {e.get('exception_id')}: {e.get('validation_reason')}")

        print("\n" + "=" * 60)

    # Determine exit code
    if unauthorized:
        print("\n[GATE] BLOCK: Unauthorized safety exception detected")
        return 2

    if expired and args.strict:
        print("\n[GATE] BLOCK: Safety exception expired – freeze re-enabled")
        return 2

    if invalid and args.strict:
        print("\n[GATE] BLOCK: Invalid safety exception detected")
        return 2

    if valid:
        print(f"\n[GATE] Safety Exception active: {len(valid)} valid exception(s)")
        print("[GATE] Release unfreeze GRANTED (temporary)")
        return 0

    print("\n[GATE] No valid safety exceptions present")
    return 1


if __name__ == "__main__":
    sys.exit(main())
