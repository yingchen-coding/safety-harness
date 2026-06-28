#!/usr/bin/env python3
"""
Generate Quarterly Safety Investment Recommendation

When alignment debt ages beyond SLO, generates strategic
investment recommendations for executive planning.

Usage:
    python scripts/generate_safety_investment_recommendation.py
    python scripts/generate_safety_investment_recommendation.py --output artifacts/quarterly_safety_investment_recommendation.md
"""

import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
SLO_PATH = ROOT / "config" / "debt_slo.yaml"
OUTPUT_PATH = ROOT / "artifacts" / "quarterly_safety_investment_recommendation.md"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def analyze_debt_patterns(debts: list, slo_config: dict) -> dict:
    """Analyze debt patterns for investment recommendations."""
    open_debts = [d for d in debts if d.get("status") == "open" or d.get("mitigation_status") == "open"]

    # Get SLO thresholds
    slo_days = slo_config.get("slo", {}).get("by_severity", {})
    default_slo = slo_config.get("slo", {}).get("max_open_days", 30)

    # Categorize debts
    aged_debts = []
    critical_debts = []
    by_principle = {}
    total_age = 0

    for d in open_debts:
        age = d.get("age_days", 0)
        severity = d.get("severity", "medium")
        principle = d.get("principle", "Unknown")

        slo = slo_days.get(severity, default_slo)

        if age > slo:
            aged_debts.append(d)

        if severity == "critical":
            critical_debts.append(d)

        by_principle[principle] = by_principle.get(principle, 0) + 1
        total_age += age

    avg_age = total_age / len(open_debts) if open_debts else 0

    # Identify systemic gaps
    systemic_gaps = []
    for principle, count in by_principle.items():
        if count >= 2:
            systemic_gaps.append({
                "principle": principle,
                "count": count,
                "indication": "Repeated debt suggests architectural gap"
            })

    return {
        "total_open": len(open_debts),
        "aged_count": len(aged_debts),
        "critical_count": len(critical_debts),
        "avg_age_days": round(avg_age, 1),
        "by_principle": by_principle,
        "systemic_gaps": systemic_gaps,
        "aged_debts": aged_debts
    }


def estimate_investment(analysis: dict) -> dict:
    """Estimate investment recommendations based on debt analysis."""
    recommendations = []
    estimated_fte = 0
    estimated_weeks = 0

    # Critical debt requires immediate attention
    if analysis["critical_count"] > 0:
        recommendations.append({
            "priority": "IMMEDIATE",
            "action": "Critical debt remediation sprint",
            "fte": 2,
            "weeks": 2,
            "rationale": f"{analysis['critical_count']} critical debt(s) require immediate engineering focus"
        })
        estimated_fte += 2
        estimated_weeks += 2

    # Aged debt indicates capacity gap
    if analysis["aged_count"] > 2:
        recommendations.append({
            "priority": "HIGH",
            "action": "Increase safety engineering headcount",
            "fte": 2,
            "weeks": 0,  # permanent
            "rationale": f"{analysis['aged_count']} debts exceeded SLO, indicating insufficient capacity"
        })
        estimated_fte += 2

    # Systemic gaps need architectural investment
    if analysis["systemic_gaps"]:
        recommendations.append({
            "priority": "HIGH",
            "action": "Safeguard architecture hardening sprint",
            "fte": 3,
            "weeks": 4,
            "rationale": f"Repeated debt in {len(analysis['systemic_gaps'])} principle(s) indicates architectural gaps"
        })
        estimated_fte += 3
        estimated_weeks += 4

    # High average age indicates review process issues
    if analysis["avg_age_days"] > 20:
        recommendations.append({
            "priority": "MEDIUM",
            "action": "Improve incident review and debt triage process",
            "fte": 1,
            "weeks": 2,
            "rationale": f"Average debt age of {analysis['avg_age_days']} days suggests review bottlenecks"
        })
        estimated_fte += 1
        estimated_weeks += 2

    # Always recommend proactive measures
    recommendations.append({
        "priority": "ONGOING",
        "action": "Red-team capacity maintenance",
        "fte": 1,
        "weeks": 0,  # permanent
        "rationale": "Continuous adversarial testing prevents debt accumulation"
    })

    return {
        "recommendations": recommendations,
        "estimated_fte": estimated_fte,
        "estimated_sprint_weeks": estimated_weeks
    }


def generate_recommendation_report(debts: list, slo_config: dict) -> str:
    """Generate markdown investment recommendation report."""
    timestamp = datetime.now(timezone.utc)
    analysis = analyze_debt_patterns(debts, slo_config)
    investment = estimate_investment(analysis)

    # Build recommendations section
    recs_md = ""
    for i, rec in enumerate(investment["recommendations"], 1):
        priority_emoji = {
            "IMMEDIATE": "🔴",
            "HIGH": "🟠",
            "MEDIUM": "🟡",
            "ONGOING": "🔵"
        }.get(rec["priority"], "⚪")

        fte_text = f"{rec['fte']} FTE"
        duration_text = f"{rec['weeks']} weeks" if rec["weeks"] > 0 else "Permanent"

        recs_md += f"""
### {i}. {priority_emoji} {rec["action"]}

- **Priority:** {rec["priority"]}
- **Resource Estimate:** {fte_text} for {duration_text}
- **Rationale:** {rec["rationale"]}
"""

    # Build aged debt evidence
    evidence_md = ""
    for d in analysis["aged_debts"][:5]:  # Top 5
        evidence_md += f"- **{d.get('debt_id', 'Unknown')}** ({d.get('principle', '?')}): {d.get('age_days', 0)} days old, severity={d.get('severity', 'unknown')}\n"

    if not evidence_md:
        evidence_md = "- No aged debts currently\n"

    # Build systemic gaps
    gaps_md = ""
    for gap in analysis["systemic_gaps"]:
        gaps_md += f"- **{gap['principle']}**: {gap['count']} occurrences - {gap['indication']}\n"

    if not gaps_md:
        gaps_md = "- No systemic patterns identified\n"

    md = f"""# Quarterly Safety Investment Recommendation

**Date:** {timestamp.strftime('%Y-%m-%d')}
**Generated:** {timestamp.isoformat()}
**Classification:** Internal - Executive Planning

---

## Executive Summary

Alignment debt analysis indicates {'significant' if analysis['aged_count'] > 2 else 'moderate' if analysis['aged_count'] > 0 else 'minimal'} safety capacity gaps requiring strategic investment.

| Metric | Value |
|--------|-------|
| Open Alignment Debts | {analysis['total_open']} |
| Debts Exceeding SLO | {analysis['aged_count']} |
| Critical Severity | {analysis['critical_count']} |
| Average Debt Age | {analysis['avg_age_days']} days |

---

## Investment Recommendations

{recs_md}

---

## Resource Summary

| Category | Estimate |
|----------|----------|
| Total FTE (sprint) | {investment['estimated_fte']} |
| Sprint Duration | {investment['estimated_sprint_weeks']} weeks |
| Estimated Cost | ${investment['estimated_fte'] * 50000 * (investment['estimated_sprint_weeks'] / 52):.0f} (sprint only) |

---

## Evidence: Aged Debts

{evidence_md}

---

## Systemic Gaps Identified

{gaps_md}

---

## Risk Framing for Board

### Without Investment

- Continued accumulation of alignment debt
- Increased probability of safety incidents
- Potential regulatory exposure as AI governance matures
- Engineering velocity impact from recurring issues

### With Investment

- Debt backlog cleared within {investment['estimated_sprint_weeks'] + 4} weeks
- Sustainable safety capacity for future releases
- Reduced incident probability
- Proactive compliance posture

---

## Recommended Board Actions

1. **Approve** safety engineering headcount increase
2. **Prioritize** critical debt remediation sprint
3. **Schedule** quarterly safety investment review
4. **Track** alignment debt as organizational KPI

---

*Generated by Model Safety Regression Suite | Constitution-as-Code Governance*
"""

    return md


def main():
    parser = argparse.ArgumentParser(
        description="Generate Quarterly Safety Investment Recommendation"
    )
    parser.add_argument(
        "--debt", "-d",
        type=Path,
        default=DEBT_PATH,
        help="Path to alignment_debt.yaml"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output markdown path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SAFETY INVESTMENT RECOMMENDATION GENERATOR")
    print("=" * 60)

    debt_data = load_yaml(args.debt)
    debts = debt_data.get("ledger", debt_data.get("debts", []))
    slo_config = load_yaml(SLO_PATH)

    md = generate_recommendation_report(debts, slo_config)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(md)

    analysis = analyze_debt_patterns(debts, slo_config)

    print(f"\n[OK] Safety investment recommendation generated: {args.output}")
    print(f"[OK] Open debts: {analysis['total_open']}")
    print(f"[OK] Aged debts: {analysis['aged_count']}")
    print(f"[OK] Critical debts: {analysis['critical_count']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
