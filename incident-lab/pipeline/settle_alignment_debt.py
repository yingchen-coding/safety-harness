"""
Settle alignment debt after incident replay verification.

Flow:
incident_replay_results.json
  → find mitigated principles
  → update alignment_debt.yaml (open → mitigated)
  → update regression-suite policy_exception.yaml (remove resolved exceptions)

This ensures:
1. No debt is cleared without verified replay
2. Policy exceptions are automatically revoked when fixes land
3. Full audit trail of what was mitigated and when

Usage:
    python pipeline/settle_alignment_debt.py
    python pipeline/settle_alignment_debt.py --replay artifacts/incident_replay_results.json
"""

import yaml
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, Set

ROOT = Path(__file__).resolve().parents[1]

# Default paths
REPLAY_RESULTS = ROOT / "artifacts" / "incident_replay_results.json"
ALIGNMENT_DEBT = ROOT.parent / "model-safety-regression-suite" / "artifacts" / "alignment_debt.yaml"
POLICY_EXCEPTIONS = ROOT.parent / "model-safety-regression-suite" / "config" / "policy_exception.yaml"


def load_yaml(path: Path) -> Dict:
    """Load YAML file, return empty dict if not found."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: Dict) -> None:
    """Save data to YAML file, creating parent dirs if needed."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def load_replay_results(path: Path) -> Dict:
    """Load incident replay verification results."""
    if not path.exists():
        raise FileNotFoundError(f"Replay results not found: {path}")
    with open(path) as f:
        return json.load(f)


def get_mitigated_principles(replay: Dict) -> Set[str]:
    """Extract principles that were successfully mitigated."""
    return {
        v["principle"]
        for v in replay.get("verified_mitigations", [])
        if v.get("status") == "pass"
    }


def update_debt_ledger(
    debt_ledger: Dict,
    mitigated_principles: Set[str],
    incident_id: str,
    verification_run_id: str
) -> int:
    """
    Update debt entries for mitigated principles.

    Returns count of updated entries.
    """
    timestamp = datetime.utcnow().isoformat() + "Z"
    updated = 0

    for debt in debt_ledger.get("ledger", []):
        principle = debt.get("principle")
        status = debt.get("mitigation_status")

        if principle in mitigated_principles and status == "open":
            debt["mitigation_status"] = "mitigated"
            debt["mitigated_by_incident"] = incident_id
            debt["verified_in_run"] = verification_run_id
            debt["mitigated_at"] = timestamp
            debt["blocks_release"] = False  # No longer blocks after mitigation
            updated += 1

    # Update summary if present
    if "summary" in debt_ledger:
        active_count = sum(
            1 for d in debt_ledger.get("ledger", [])
            if d.get("mitigation_status") not in ("mitigated", "accepted")
        )
        mitigated_count = sum(
            1 for d in debt_ledger.get("ledger", [])
            if d.get("mitigation_status") == "mitigated"
        )
        debt_ledger["summary"]["active_entries"] = active_count
        debt_ledger["summary"]["mitigated_entries"] = mitigated_count
        debt_ledger["summary"]["last_updated"] = timestamp

    return updated


def update_policy_exceptions(
    exceptions: Dict,
    mitigated_principles: Set[str]
) -> int:
    """
    Remove policy exceptions for mitigated principles.

    Returns count of removed exceptions.
    """
    before = len(exceptions.get("exceptions", []))

    exceptions["exceptions"] = [
        e for e in exceptions.get("exceptions", [])
        if e.get("principle") not in mitigated_principles
    ]

    after = len(exceptions.get("exceptions", []))

    # Add audit trail
    if before > after:
        exceptions.setdefault("audit_log", []).append({
            "action": "exceptions_removed",
            "count": before - after,
            "principles": list(mitigated_principles),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        })

    return before - after


def settle_debt(
    replay_path: Path = REPLAY_RESULTS,
    debt_path: Path = ALIGNMENT_DEBT,
    exceptions_path: Path = POLICY_EXCEPTIONS,
    dry_run: bool = False
) -> Dict:
    """
    Main settlement function.

    Args:
        replay_path: Path to replay results JSON
        debt_path: Path to alignment debt YAML
        exceptions_path: Path to policy exceptions YAML
        dry_run: If True, don't write changes

    Returns:
        Summary of actions taken
    """
    # Load data
    replay = load_replay_results(replay_path)
    debt_ledger = load_yaml(debt_path)
    exceptions = load_yaml(exceptions_path)

    # Get mitigated principles
    mitigated = get_mitigated_principles(replay)

    if not mitigated:
        return {
            "status": "no_action",
            "message": "No verified mitigations found in replay results"
        }

    # Update debt ledger
    debts_updated = update_debt_ledger(
        debt_ledger,
        mitigated,
        replay.get("incident_id", "unknown"),
        replay.get("verification_run_id", "unknown")
    )

    # Update policy exceptions
    exceptions_removed = update_policy_exceptions(exceptions, mitigated)

    # Save changes (unless dry run)
    if not dry_run:
        save_yaml(debt_path, debt_ledger)
        save_yaml(exceptions_path, exceptions)

    return {
        "status": "success",
        "incident_id": replay.get("incident_id"),
        "verification_run_id": replay.get("verification_run_id"),
        "mitigated_principles": list(mitigated),
        "debts_updated": debts_updated,
        "exceptions_removed": exceptions_removed,
        "dry_run": dry_run
    }


def main():
    parser = argparse.ArgumentParser(
        description="Settle alignment debt after incident replay verification"
    )
    parser.add_argument(
        "--replay", "-r",
        type=Path,
        default=REPLAY_RESULTS,
        help="Path to replay results JSON"
    )
    parser.add_argument(
        "--debt", "-d",
        type=Path,
        default=ALIGNMENT_DEBT,
        help="Path to alignment debt YAML"
    )
    parser.add_argument(
        "--exceptions", "-e",
        type=Path,
        default=POLICY_EXCEPTIONS,
        help="Path to policy exceptions YAML"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be changed without writing"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ALIGNMENT DEBT SETTLEMENT")
    print("=" * 60)

    try:
        result = settle_debt(
            replay_path=args.replay,
            debt_path=args.debt,
            exceptions_path=args.exceptions,
            dry_run=args.dry_run
        )

        if result["status"] == "no_action":
            print(f"\n[SKIP] {result['message']}")
        else:
            print(f"\n[OK] Incident: {result['incident_id']}")
            print(f"[OK] Verification run: {result['verification_run_id']}")
            print(f"[OK] Mitigated principles: {', '.join(result['mitigated_principles'])}")
            print(f"[OK] Debts updated: {result['debts_updated']}")
            print(f"[OK] Exceptions removed: {result['exceptions_removed']}")

            if result["dry_run"]:
                print("\n[DRY RUN] No changes written")
            else:
                print("\n[OK] Alignment debt and policy exceptions updated")

    except FileNotFoundError as e:
        print(f"\n[ERROR] {e}")
        return 1

    print("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
