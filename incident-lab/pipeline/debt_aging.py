"""
Alignment Debt Aging and SLO Enforcement

Tracks debt age and enforces organizational SLOs:
- debt > N days without progress → escalate
- debt > M days → auto-BLOCK release
- aging curve data for dashboard/KPI

This transforms alignment debt from "technical note" into
"organizational accountability mechanism".

SLO Thresholds (configurable):
- WARNING: debt open > 14 days
- ESCALATE: debt open > 30 days
- BLOCK: debt open > 45 days (critical) or > 60 days (high)

Usage:
    python pipeline/debt_aging.py --check      # Check SLO violations
    python pipeline/debt_aging.py --enforce    # Enforce blocking rules
    python pipeline/debt_aging.py --report     # Generate aging report
    python pipeline/debt_aging.py --dashboard  # Export dashboard data
"""

import yaml
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

ROOT = Path(__file__).resolve().parents[1]
ALIGNMENT_DEBT = ROOT.parent / "model-safety-regression-suite" / "artifacts" / "alignment_debt.yaml"
AGING_REPORT = ROOT / "artifacts" / "debt_aging_report.json"


class SLOStatus(Enum):
    """SLO compliance status."""
    OK = "ok"
    WARNING = "warning"
    ESCALATE = "escalate"
    BLOCK = "block"


@dataclass
class AgingConfig:
    """SLO thresholds for debt aging."""
    warning_days: int = 14
    escalate_days: int = 30
    block_days_critical: int = 45
    block_days_high: int = 60
    block_days_medium: int = 90


@dataclass
class DebtAgingEntry:
    """Aging analysis for a single debt entry."""
    debt_id: str
    principle: str
    severity: str
    created_at: str
    age_days: int
    slo_status: str
    days_until_block: Optional[int]
    owner: Optional[str]
    mitigation_status: str


def load_yaml(path: Path) -> Dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def save_yaml(path: Path, data: Dict) -> None:
    """Save YAML file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.safe_dump(data, f, default_flow_style=False, sort_keys=False)


def parse_timestamp(ts: str) -> datetime:
    """Parse ISO timestamp."""
    # Handle various formats
    ts = ts.rstrip("Z")
    for fmt in ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"]:
        try:
            return datetime.strptime(ts, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse timestamp: {ts}")


def calculate_age_days(created_at: str, now: Optional[datetime] = None) -> int:
    """Calculate age in days from creation timestamp."""
    now = now or datetime.utcnow()
    created = parse_timestamp(created_at)
    return (now - created).days


def get_slo_status(
    age_days: int,
    severity: str,
    config: AgingConfig
) -> Tuple[SLOStatus, Optional[int]]:
    """
    Determine SLO status and days until block.

    Returns (status, days_until_block).
    """
    # Determine block threshold based on severity
    if severity == "critical":
        block_threshold = config.block_days_critical
    elif severity == "high":
        block_threshold = config.block_days_high
    else:
        block_threshold = config.block_days_medium

    days_until_block = block_threshold - age_days

    if age_days >= block_threshold:
        return SLOStatus.BLOCK, 0
    elif age_days >= config.escalate_days:
        return SLOStatus.ESCALATE, days_until_block
    elif age_days >= config.warning_days:
        return SLOStatus.WARNING, days_until_block
    else:
        return SLOStatus.OK, days_until_block


def analyze_debt_aging(
    debt_ledger: Dict,
    config: Optional[AgingConfig] = None,
    now: Optional[datetime] = None
) -> List[DebtAgingEntry]:
    """
    Analyze aging for all debt entries.

    Returns list of aging entries with SLO status.
    """
    config = config or AgingConfig()
    now = now or datetime.utcnow()
    entries = []

    for debt in debt_ledger.get("ledger", []):
        # Skip already mitigated/accepted debt
        mitigation_status = debt.get("mitigation_status", "open")
        if mitigation_status in ("mitigated", "accepted"):
            continue

        created_at = debt.get("created_at", now.isoformat())
        age_days = calculate_age_days(created_at, now)
        severity = debt.get("severity", "medium")

        slo_status, days_until_block = get_slo_status(age_days, severity, config)

        # Get owner from planned_resolution if available
        owner = None
        if "planned_resolution" in debt:
            owner = debt["planned_resolution"].get("owner")

        entries.append(DebtAgingEntry(
            debt_id=debt.get("debt_id", "unknown"),
            principle=debt.get("principle", "unknown"),
            severity=severity,
            created_at=created_at,
            age_days=age_days,
            slo_status=slo_status.value,
            days_until_block=days_until_block,
            owner=owner,
            mitigation_status=mitigation_status
        ))

    return entries


def enforce_aging_blocks(
    debt_ledger: Dict,
    config: Optional[AgingConfig] = None
) -> int:
    """
    Enforce blocking rules for aged debt.

    Sets blocks_release=True for debt that exceeds SLO.
    Returns count of entries updated.
    """
    config = config or AgingConfig()
    now = datetime.utcnow()
    updated = 0

    for debt in debt_ledger.get("ledger", []):
        mitigation_status = debt.get("mitigation_status", "open")
        if mitigation_status in ("mitigated", "accepted"):
            continue

        created_at = debt.get("created_at", now.isoformat())
        age_days = calculate_age_days(created_at, now)
        severity = debt.get("severity", "medium")

        slo_status, _ = get_slo_status(age_days, severity, config)

        if slo_status == SLOStatus.BLOCK and not debt.get("blocks_release"):
            debt["blocks_release"] = True
            debt["block_reason"] = f"SLO exceeded: {age_days} days without resolution"
            updated += 1

    return updated


def generate_aging_report(
    entries: List[DebtAgingEntry],
    config: Optional[AgingConfig] = None
) -> Dict:
    """Generate comprehensive aging report."""
    config = config or AgingConfig()

    # Group by status
    by_status = {s.value: [] for s in SLOStatus}
    for entry in entries:
        by_status[entry.slo_status].append(asdict(entry))

    # Calculate summary stats
    total_age = sum(e.age_days for e in entries)
    avg_age = total_age / len(entries) if entries else 0

    # Debt by principle
    by_principle = {}
    for entry in entries:
        p = entry.principle
        by_principle[p] = by_principle.get(p, 0) + 1

    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "config": asdict(config),
        "summary": {
            "total_active_debt": len(entries),
            "average_age_days": round(avg_age, 1),
            "oldest_age_days": max((e.age_days for e in entries), default=0),
            "blocking_count": len(by_status[SLOStatus.BLOCK.value]),
            "escalation_count": len(by_status[SLOStatus.ESCALATE.value]),
            "warning_count": len(by_status[SLOStatus.WARNING.value]),
        },
        "by_status": by_status,
        "by_principle": by_principle,
        "slo_violations": [
            asdict(e) for e in entries
            if e.slo_status in (SLOStatus.BLOCK.value, SLOStatus.ESCALATE.value)
        ]
    }


def export_dashboard_data(
    entries: List[DebtAgingEntry],
    output_path: Path
) -> None:
    """Export data for dashboard visualization."""
    # Aging curve data (days -> count)
    aging_curve = {}
    for entry in entries:
        bucket = (entry.age_days // 7) * 7  # Weekly buckets
        aging_curve[bucket] = aging_curve.get(bucket, 0) + 1

    # Severity distribution
    severity_dist = {}
    for entry in entries:
        severity_dist[entry.severity] = severity_dist.get(entry.severity, 0) + 1

    dashboard_data = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "kpis": {
            "total_debt_count": len(entries),
            "blocking_debt_count": sum(1 for e in entries if e.slo_status == SLOStatus.BLOCK.value),
            "avg_debt_age_days": round(sum(e.age_days for e in entries) / len(entries), 1) if entries else 0,
            "debt_velocity": "TODO: calculate from historical data"
        },
        "aging_curve": [
            {"days": days, "count": count}
            for days, count in sorted(aging_curve.items())
        ],
        "severity_distribution": severity_dist,
        "entries": [asdict(e) for e in entries]
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dashboard_data, f, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Alignment Debt Aging and SLO Enforcement"
    )
    parser.add_argument(
        "--debt", "-d",
        type=Path,
        default=ALIGNMENT_DEBT,
        help="Path to alignment debt YAML"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check SLO violations without enforcing"
    )
    parser.add_argument(
        "--enforce",
        action="store_true",
        help="Enforce blocking rules for aged debt"
    )
    parser.add_argument(
        "--report",
        action="store_true",
        help="Generate aging report"
    )
    parser.add_argument(
        "--dashboard",
        action="store_true",
        help="Export dashboard data"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=AGING_REPORT,
        help="Output path for report/dashboard"
    )
    args = parser.parse_args()

    debt_ledger = load_yaml(args.debt)
    config = AgingConfig()
    entries = analyze_debt_aging(debt_ledger, config)

    print("=" * 60)
    print("ALIGNMENT DEBT AGING ANALYSIS")
    print("=" * 60)
    print(f"\nActive debt entries: {len(entries)}")

    if not entries:
        print("[OK] No active debt to analyze")
        return 0

    # Display summary
    violations = [e for e in entries if e.slo_status in (SLOStatus.BLOCK.value, SLOStatus.ESCALATE.value)]
    warnings = [e for e in entries if e.slo_status == SLOStatus.WARNING.value]

    if violations:
        print(f"\n[ALERT] SLO VIOLATIONS: {len(violations)}")
        for e in violations:
            print(f"  - {e.debt_id}: {e.age_days} days ({e.slo_status.upper()})")
            print(f"    Principle: {e.principle} | Owner: {e.owner or 'unassigned'}")

    if warnings:
        print(f"\n[WARN] Approaching SLO: {len(warnings)}")
        for e in warnings:
            print(f"  - {e.debt_id}: {e.age_days} days (blocks in {e.days_until_block} days)")

    if args.enforce:
        updated = enforce_aging_blocks(debt_ledger, config)
        if updated > 0:
            save_yaml(args.debt, debt_ledger)
            print(f"\n[ENFORCE] Updated {updated} entries to blocking status")
        else:
            print("\n[ENFORCE] No updates needed")

    if args.report:
        report = generate_aging_report(entries, config)
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        print(f"\n[REPORT] Saved to {args.output}")

    if args.dashboard:
        dashboard_path = args.output.with_suffix(".dashboard.json")
        export_dashboard_data(entries, dashboard_path)
        print(f"\n[DASHBOARD] Exported to {dashboard_path}")

    print("\n" + "=" * 60)

    # Exit with appropriate code
    if any(e.slo_status == SLOStatus.BLOCK.value for e in entries):
        return 2  # BLOCK
    elif violations:
        return 1  # WARN
    return 0


if __name__ == "__main__":
    exit(main())
