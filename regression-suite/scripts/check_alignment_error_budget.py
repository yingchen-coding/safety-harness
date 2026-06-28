#!/usr/bin/env python3
"""
Alignment Error Budget Enforcement.

Block release if new alignment debts introduced this quarter exceed budget.
This is the "Error Budget for AI Safety" - analogous to SRE error budgets.

Exit codes:
    0 = OK (within budget)
    1 = WARN (approaching budget)
    2 = BLOCK (budget exceeded)

Usage:
    python scripts/check_alignment_error_budget.py
    python scripts/check_alignment_error_budget.py --dry-run
"""

import yaml
import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple

ROOT = Path(__file__).resolve().parents[1]

DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
CONFIG_PATH = ROOT / "config" / "alignment_error_budget.yaml"
DASHBOARD_PATH = ROOT / "dashboard" / "alignment_error_budget.json"


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def current_quarter(dt: datetime) -> str:
    """Get current quarter string (e.g., '2026-Q1')."""
    return f"{dt.year}-Q{((dt.month - 1) // 3) + 1}"


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp."""
    ts = ts.rstrip("Z")
    if "+" in ts:
        ts = ts.split("+")[0]
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"]:
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp: {ts}")


def calculate_weighted_budget(debts: List[Dict], weights: Dict) -> float:
    """Calculate weighted budget consumption."""
    total = 0.0
    for d in debts:
        severity = d.get("severity", "medium")
        weight = weights.get(severity, 1.0)
        total += weight
    return total


def check_error_budget(
    debt_ledger: Dict,
    config: Dict,
    now: datetime = None
) -> Tuple[float, float, bool, List[Dict]]:
    """
    Check error budget status.

    Returns (used, total, exceeded, debts_this_quarter).
    """
    now = now or datetime.now(timezone.utc)
    quarter = current_quarter(now)

    budget_config = config.get("error_budget", {})
    max_budget = budget_config.get("max_new_alignment_debts", 2)
    weights = budget_config.get("severity_weights", {
        "critical": 3.0, "high": 1.0, "medium": 0.5, "low": 0.25
    })

    # Find debts introduced this quarter
    debts_this_quarter = []
    for debt in debt_ledger.get("ledger", []):
        introduced_at = debt.get("introduced_at") or debt.get("created_at")
        if not introduced_at:
            continue

        try:
            introduced = parse_timestamp(introduced_at)
            if current_quarter(introduced) == quarter:
                debts_this_quarter.append(debt)
        except ValueError:
            continue

    # Calculate weighted consumption
    used = calculate_weighted_budget(debts_this_quarter, weights)
    exceeded = used > max_budget

    return used, max_budget, exceeded, debts_this_quarter


def export_dashboard_data(
    used: float,
    total: float,
    exceeded: bool,
    debts: List[Dict],
    quarter: str,
    output_path: Path
) -> None:
    """Export dashboard data."""
    now = datetime.now(timezone.utc)

    utilization_pct = (used / total * 100) if total > 0 else 0

    dashboard_data = {
        "generated_at": now.isoformat(),
        "quarter": quarter,
        "budget": {
            "used": round(used, 2),
            "total": total,
            "remaining": round(max(0, total - used), 2),
            "utilization_pct": round(utilization_pct, 1),
            "exceeded": exceeded
        },
        "debts_this_quarter": [
            {
                "debt_id": d.get("debt_id"),
                "principle": d.get("principle"),
                "severity": d.get("severity"),
                "introduced_at": d.get("introduced_at") or d.get("created_at"),
                "mechanism_gap": d.get("mechanism_gap")
            }
            for d in debts
        ],
        "status": "EXCEEDED" if exceeded else ("WARNING" if utilization_pct >= 80 else "OK")
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dashboard_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Check Alignment Error Budget"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check without exporting dashboard data"
    )
    parser.add_argument(
        "--debt", "-d",
        type=Path,
        default=DEBT_PATH,
        help="Path to alignment debt YAML"
    )
    parser.add_argument(
        "--config", "-c",
        type=Path,
        default=CONFIG_PATH,
        help="Path to error budget configuration"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DASHBOARD_PATH,
        help="Path to dashboard output"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ALIGNMENT ERROR BUDGET CHECK")
    print("=" * 60)

    now = datetime.now(timezone.utc)
    quarter = current_quarter(now)

    debt_ledger = load_yaml(args.debt)
    config = load_yaml(args.config)

    used, total, exceeded, debts = check_error_budget(debt_ledger, config, now)

    utilization_pct = (used / total * 100) if total > 0 else 0

    print(f"\nQuarter: {quarter}")
    print(f"Budget: {used:.1f} / {total} ({utilization_pct:.1f}% utilized)")
    print(f"Debts introduced this quarter: {len(debts)}")

    if debts:
        print("\nDebts this quarter:")
        for d in debts:
            print(f"  - {d.get('debt_id')}: {d.get('principle')} ({d.get('severity')})")

    if not args.dry_run:
        export_dashboard_data(used, total, exceeded, debts, quarter, args.output)
        print(f"\n[OK] Dashboard data exported to {args.output}")

    print("\n" + "=" * 60)

    # Determine exit code
    budget_config = config.get("error_budget", {})
    block_on_exceed = budget_config.get("block_on_exceed", True)

    if exceeded and block_on_exceed:
        print(f"\n[GATE] BLOCK: Alignment Error Budget exceeded ({used:.1f} / {total} in {quarter})")
        print("[GATE] Feature releases frozen until debt is resolved")
        return 2
    elif utilization_pct >= 80:
        print(f"\n[GATE] WARN: Approaching budget limit ({utilization_pct:.1f}% utilized)")
        return 1
    else:
        print(f"\n[GATE] OK: Within error budget ({used:.1f} / {total} in {quarter})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
