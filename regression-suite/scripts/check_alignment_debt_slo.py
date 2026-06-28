#!/usr/bin/env python3
"""
Check alignment debt aging against SLO.

Annotates debts with age_days + slo_breached.
Returns exit code 2 (BLOCK) if breached.

Integration:
- Called by release gate before verdict
- Outputs dashboard data for visualization
- Exit codes: 0=OK, 1=WARN, 2=BLOCK

Usage:
    python scripts/check_alignment_debt_slo.py
    python scripts/check_alignment_debt_slo.py --dry-run
"""

import yaml
import json
import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

ROOT = Path(__file__).resolve().parents[1]

DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
SLO_PATH = ROOT / "config" / "debt_slo.yaml"
DASHBOARD_PATH = ROOT / "dashboard" / "alignment_debt_aging.json"


def load_yaml(path: Path) -> Dict:
    """Load YAML file, return empty dict if not found."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: Dict) -> None:
    """Save data to YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp to datetime."""
    ts = ts.rstrip("Z")
    if "+" in ts:
        ts = ts.split("+")[0]
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"]:
        try:
            return datetime.strptime(ts, fmt).replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp: {ts}")


def get_slo_days(severity: str, slo_config: Dict) -> int:
    """Get SLO days for a given severity."""
    by_severity = slo_config.get("by_severity", {})
    defaults = {"critical": 14, "high": 30, "medium": 60, "low": 90}
    return by_severity.get(severity, defaults.get(severity, 30))


def check_debt_slo(
    debt_ledger: Dict,
    slo_config: Dict,
    now: Optional[datetime] = None
) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Check all debts against SLO.

    Returns (breached, warning, ok) lists.
    """
    now = now or datetime.now(timezone.utc)
    warning_days = slo_config.get("warning_before_days", 7)

    breached = []
    warning = []
    ok = []

    for debt in debt_ledger.get("ledger", []):
        # Skip already mitigated/accepted debt
        status = debt.get("mitigation_status", "open")
        if status in ("mitigated", "accepted"):
            continue

        # Get creation timestamp
        introduced_at = debt.get("introduced_at") or debt.get("created_at")
        if not introduced_at:
            # Default to recent if no timestamp
            introduced_at = now.isoformat()

        try:
            introduced = parse_timestamp(introduced_at)
        except ValueError:
            introduced = now

        # Calculate age
        age_days = (now - introduced).days
        debt["age_days"] = age_days

        # Get severity-specific SLO
        severity = debt.get("severity", "medium")
        slo_days = get_slo_days(severity, slo_config)
        debt["slo_days"] = slo_days

        # Check SLO status
        days_remaining = slo_days - age_days
        debt["days_until_slo"] = days_remaining

        if age_days > slo_days:
            debt["slo_breached"] = True
            debt["slo_status"] = "BREACHED"
            breached.append(debt)
        elif days_remaining <= warning_days:
            debt["slo_breached"] = False
            debt["slo_status"] = "WARNING"
            warning.append(debt)
        else:
            debt["slo_breached"] = False
            debt["slo_status"] = "OK"
            ok.append(debt)

    return breached, warning, ok


def calculate_kpis(
    debt_ledger: Dict,
    slo_config: Dict,
    breached: List[Dict],
    warning: List[Dict],
    ok: List[Dict]
) -> Dict:
    """Calculate organizational safety KPIs."""
    kpi_config = slo_config.get("kpi", {})

    open_debts = breached + warning + ok
    high_severity = [d for d in open_debts if d.get("severity") in ("critical", "high")]

    # Calculate average age
    total_age = sum(d.get("age_days", 0) for d in open_debts)
    avg_age = total_age / len(open_debts) if open_debts else 0

    # Check against targets
    target = kpi_config.get("debt_backlog_target", 0)
    warn_threshold = kpi_config.get("warn_threshold", 1)
    critical_threshold = kpi_config.get("critical_threshold", 3)

    if len(open_debts) > critical_threshold:
        health_status = "CRITICAL"
    elif len(open_debts) > warn_threshold:
        health_status = "WARNING"
    elif len(open_debts) > target:
        health_status = "ACCEPTABLE"
    else:
        health_status = "HEALTHY"

    return {
        "total_open": len(open_debts),
        "high_severity_open": len(high_severity),
        "slo_breached": len(breached),
        "approaching_slo": len(warning),
        "average_age_days": round(avg_age, 1),
        "oldest_debt_days": max((d.get("age_days", 0) for d in open_debts), default=0),
        "health_status": health_status,
        "target": target,
        "error_budget_remaining": max(0, kpi_config.get("quarterly_error_budget", 5) - len(open_debts))
    }


def export_dashboard_data(
    breached: List[Dict],
    warning: List[Dict],
    ok: List[Dict],
    kpis: Dict,
    slo_config: Dict,
    output_path: Path
) -> None:
    """Export dashboard visualization data."""
    now = datetime.now(timezone.utc)

    all_debts = breached + warning + ok

    # Age distribution for histogram
    age_buckets = {}
    for debt in all_debts:
        age = debt.get("age_days", 0)
        bucket = (age // 7) * 7  # Weekly buckets
        age_buckets[bucket] = age_buckets.get(bucket, 0) + 1

    # Severity distribution
    severity_dist = {}
    for debt in all_debts:
        sev = debt.get("severity", "unknown")
        severity_dist[sev] = severity_dist.get(sev, 0) + 1

    # Principle distribution
    principle_dist = {}
    for debt in all_debts:
        p = debt.get("principle", "unknown")
        principle_dist[p] = principle_dist.get(p, 0) + 1

    dashboard_data = {
        "generated_at": now.isoformat(),
        "slo_config": {
            "max_open_days": slo_config.get("max_open_days", 30),
            "by_severity": slo_config.get("by_severity", {})
        },
        "kpis": kpis,
        "open_debts": [
            {
                "debt_id": d.get("debt_id"),
                "principle": d.get("principle"),
                "severity": d.get("severity"),
                "age_days": d.get("age_days"),
                "slo_days": d.get("slo_days"),
                "days_until_slo": d.get("days_until_slo"),
                "slo_status": d.get("slo_status"),
                "mechanism_gap": d.get("mechanism_gap")
            }
            for d in all_debts
        ],
        "distributions": {
            "age_histogram": [
                {"bucket_start": k, "count": v}
                for k, v in sorted(age_buckets.items())
            ],
            "by_severity": severity_dist,
            "by_principle": principle_dist
        }
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dashboard_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Check alignment debt against SLO"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Check without modifying files"
    )
    parser.add_argument(
        "--debt", "-d",
        type=Path,
        default=DEBT_PATH,
        help="Path to alignment debt YAML"
    )
    parser.add_argument(
        "--slo", "-s",
        type=Path,
        default=SLO_PATH,
        help="Path to SLO configuration"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=DASHBOARD_PATH,
        help="Path to dashboard output"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("ALIGNMENT DEBT SLO CHECK")
    print("=" * 60)

    # Load configuration
    debt_ledger = load_yaml(args.debt)
    slo_config = load_yaml(args.slo).get("slo", {})

    if not debt_ledger.get("ledger"):
        print("\n[OK] No alignment debt found")
        return 0

    # Check SLO
    breached, warning, ok = check_debt_slo(debt_ledger, slo_config)

    # Calculate KPIs
    kpis = calculate_kpis(debt_ledger, slo_config, breached, warning, ok)

    # Display results
    print(f"\nOpen Debts: {kpis['total_open']}")
    print(f"High Severity: {kpis['high_severity_open']}")
    print(f"Average Age: {kpis['average_age_days']} days")
    print(f"Health Status: {kpis['health_status']}")

    if breached:
        print(f"\n[BLOCK] SLO BREACHED: {len(breached)} debts exceeded SLO")
        for d in breached:
            print(f"  - {d.get('debt_id')}: {d.get('age_days')} days (SLO: {d.get('slo_days')})")
            print(f"    Principle: {d.get('principle')} | Severity: {d.get('severity')}")

    if warning:
        print(f"\n[WARN] Approaching SLO: {len(warning)} debts")
        for d in warning:
            print(f"  - {d.get('debt_id')}: {d.get('days_until_slo')} days remaining")

    # Save updated debt ledger (with age annotations)
    if not args.dry_run:
        save_yaml(args.debt, debt_ledger)
        export_dashboard_data(breached, warning, ok, kpis, slo_config, args.output)
        print(f"\n[OK] Dashboard data exported to {args.output}")
    else:
        print("\n[DRY RUN] No changes written")

    print("\n" + "=" * 60)

    # Exit code based on SLO status
    if breached and slo_config.get("block_on_breach", True):
        print(f"\n[GATE] BLOCK: {len(breached)} alignment debts exceeded SLO")
        return 2
    elif warning:
        print(f"\n[GATE] WARN: {len(warning)} debts approaching SLO")
        return 1
    else:
        print("\n[GATE] OK: All debts within SLO")
        return 0


if __name__ == "__main__":
    sys.exit(main())
