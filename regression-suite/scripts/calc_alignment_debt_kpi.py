#!/usr/bin/env python3
"""
Calculate Alignment Debt KPIs for organizational reporting.

Provides metrics for:
- Safety debt backlog
- Resolution velocity
- Error budget consumption
- Health status

Usage:
    python scripts/calc_alignment_debt_kpi.py
    python scripts/calc_alignment_debt_kpi.py --json
    python scripts/calc_alignment_debt_kpi.py --quarterly
"""

import yaml
import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict

ROOT = Path(__file__).resolve().parents[1]
DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
SLO_PATH = ROOT / "config" / "debt_slo.yaml"


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def calculate_kpis(debt_ledger: Dict, slo_config: Dict) -> Dict:
    """Calculate comprehensive KPIs."""
    ledger = debt_ledger.get("ledger", [])
    kpi_config = slo_config.get("kpi", {})

    # Categorize debts
    open_debts = [d for d in ledger if d.get("mitigation_status") == "open"]
    mitigated = [d for d in ledger if d.get("mitigation_status") == "mitigated"]
    accepted = [d for d in ledger if d.get("mitigation_status") == "accepted"]

    # By severity
    critical = [d for d in open_debts if d.get("severity") == "critical"]
    high = [d for d in open_debts if d.get("severity") == "high"]
    medium = [d for d in open_debts if d.get("severity") == "medium"]
    low = [d for d in open_debts if d.get("severity") == "low"]

    # By principle
    by_principle = {}
    for d in open_debts:
        p = d.get("principle", "unknown")
        by_principle[p] = by_principle.get(p, 0) + 1

    # Calculate ages
    now = datetime.now(timezone.utc)
    ages = []
    for d in open_debts:
        created = d.get("introduced_at") or d.get("created_at")
        if created:
            try:
                created_dt = datetime.fromisoformat(created.rstrip("Z")).replace(tzinfo=timezone.utc)
                ages.append((now - created_dt).days)
            except Exception:
                pass

    avg_age = sum(ages) / len(ages) if ages else 0
    max_age = max(ages) if ages else 0

    # Error budget
    quarterly_budget = kpi_config.get("quarterly_error_budget", 5)
    budget_consumed = len(open_debts)
    budget_remaining = max(0, quarterly_budget - budget_consumed)
    budget_utilization = budget_consumed / quarterly_budget if quarterly_budget > 0 else 0

    # Health status
    warn_threshold = kpi_config.get("warn_threshold", 1)
    critical_threshold = kpi_config.get("critical_threshold", 3)

    if len(critical) > 0 or budget_remaining == 0:
        health = "CRITICAL"
    elif len(high) > 2 or len(open_debts) > critical_threshold:
        health = "UNHEALTHY"
    elif len(open_debts) > warn_threshold:
        health = "WARNING"
    elif len(open_debts) > 0:
        health = "ACCEPTABLE"
    else:
        health = "HEALTHY"

    return {
        "timestamp": now.isoformat(),
        "summary": {
            "total_open": len(open_debts),
            "total_mitigated": len(mitigated),
            "total_accepted": len(accepted),
            "health_status": health
        },
        "by_severity": {
            "critical": len(critical),
            "high": len(high),
            "medium": len(medium),
            "low": len(low)
        },
        "by_principle": by_principle,
        "aging": {
            "average_age_days": round(avg_age, 1),
            "oldest_debt_days": max_age,
            "ages": sorted(ages, reverse=True)[:5]  # Top 5 oldest
        },
        "error_budget": {
            "quarterly_budget": quarterly_budget,
            "consumed": budget_consumed,
            "remaining": budget_remaining,
            "utilization_pct": round(budget_utilization * 100, 1)
        },
        "blocking": {
            "release_blocked": len(critical) > 0 or any(d.get("blocks_release") for d in open_debts),
            "blocking_debts": [
                d.get("debt_id") for d in open_debts
                if d.get("blocks_release") or d.get("severity") == "critical"
            ]
        }
    }


def print_report(kpis: Dict) -> None:
    """Print human-readable KPI report."""
    print("=" * 60)
    print("ALIGNMENT DEBT KPI REPORT")
    print("=" * 60)

    summary = kpis["summary"]
    print(f"\nHealth Status: {summary['health_status']}")
    print(f"Open Debts: {summary['total_open']}")
    print(f"Mitigated: {summary['total_mitigated']}")

    print("\n--- By Severity ---")
    for sev, count in kpis["by_severity"].items():
        indicator = "🔴" if sev == "critical" and count > 0 else "⚪"
        print(f"  {indicator} {sev.capitalize()}: {count}")

    print("\n--- By Principle ---")
    for principle, count in sorted(kpis["by_principle"].items()):
        print(f"  {principle}: {count}")

    print("\n--- Aging ---")
    aging = kpis["aging"]
    print(f"  Average Age: {aging['average_age_days']} days")
    print(f"  Oldest Debt: {aging['oldest_debt_days']} days")

    print("\n--- Error Budget ---")
    budget = kpis["error_budget"]
    print(f"  Quarterly Budget: {budget['quarterly_budget']}")
    print(f"  Consumed: {budget['consumed']}")
    print(f"  Remaining: {budget['remaining']}")
    print(f"  Utilization: {budget['utilization_pct']}%")

    if budget["utilization_pct"] >= 80:
        print("  ⚠️  Error budget nearly exhausted!")

    print("\n--- Release Status ---")
    blocking = kpis["blocking"]
    if blocking["release_blocked"]:
        print("  ❌ RELEASE BLOCKED")
        print(f"  Blocking debts: {', '.join(blocking['blocking_debts'])}")
    else:
        print("  ✅ Release not blocked by debt")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Calculate Alignment Debt KPIs"
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output as JSON"
    )
    parser.add_argument(
        "--quarterly",
        action="store_true",
        help="Include quarterly trend data"
    )
    parser.add_argument(
        "--debt", "-d",
        type=Path,
        default=DEBT_PATH,
        help="Path to alignment debt YAML"
    )
    args = parser.parse_args()

    debt_ledger = load_yaml(args.debt)
    slo_config = load_yaml(SLO_PATH)

    kpis = calculate_kpis(debt_ledger, slo_config)

    if args.json:
        print(json.dumps(kpis, indent=2))
    else:
        print_report(kpis)

    # Exit code based on health
    health = kpis["summary"]["health_status"]
    if health == "CRITICAL":
        return 2
    elif health in ("UNHEALTHY", "WARNING"):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
