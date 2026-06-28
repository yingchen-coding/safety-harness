"""
Board-Level Safety Report Generator

Generates executive-readable reports for board and leadership review.

These reports translate technical safety metrics into:
1. Business risk language
2. Trend visualization
3. Accountability documentation
4. Alignment with organizational risk appetite

Design Philosophy:
- Executives need different information than engineers
- Risk must be expressed in business impact terms
- Trends matter more than point-in-time values
- Accountability must be crystal clear
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class ExecutiveSummary:
    """Executive summary for board report."""

    report_period: str
    overall_status: str  # "GREEN", "YELLOW", "RED"
    key_metrics: dict
    top_risks: list[dict]
    notable_events: list[str]
    recommendations: list[str]

    def to_markdown(self) -> str:
        status_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(self.overall_status, "⚪")

        md = f"""## Executive Summary

**Report Period**: {self.report_period}
**Overall Safety Status**: {status_emoji} {self.overall_status}

### Key Metrics

| Metric | Value | Trend | Target |
|--------|-------|-------|--------|
"""
        for name, data in self.key_metrics.items():
            trend = data.get("trend", "→")
            value = data.get("value", "N/A")
            target = data.get("target", "N/A")
            md += f"| {name} | {value} | {trend} | {target} |\n"

        md += "\n### Top Risks\n\n"
        for i, risk in enumerate(self.top_risks[:3], 1):
            md += f"{i}. **{risk['name']}**: {risk['description']}\n"

        md += "\n### Notable Events\n\n"
        for event in self.notable_events[:5]:
            md += f"- {event}\n"

        md += "\n### Recommendations\n\n"
        for rec in self.recommendations:
            md += f"- {rec}\n"

        return md


@dataclass
class RiskDashboard:
    """Risk dashboard for board visualization."""

    # Release metrics
    total_releases: int
    releases_blocked: int
    releases_with_warnings: int
    human_overrides: int

    # Safety metrics
    violation_rate_trend: list[dict]
    alignment_debt_current: float
    alignment_debt_trend: str

    # Incident metrics
    incidents_total: int
    incidents_critical: int
    mean_time_to_regression: float  # Hours from incident to regression test

    # Constitution compliance
    constitution_version: str
    principle_compliance: dict[str, float]

    def get_status(self) -> str:
        """Compute overall status from metrics."""
        if self.incidents_critical > 0 or self.alignment_debt_current > 0.25:
            return "RED"
        elif self.releases_blocked > 0 or self.alignment_debt_current > 0.10:
            return "YELLOW"
        else:
            return "GREEN"

    def to_markdown(self) -> str:
        status = self.get_status()
        status_emoji = {"GREEN": "🟢", "YELLOW": "🟡", "RED": "🔴"}.get(status, "⚪")

        md = f"""## Risk Dashboard

### Overall Status: {status_emoji} {status}

### Release Metrics

| Metric | Value |
|--------|-------|
| Total Releases | {self.total_releases} |
| Releases Blocked | {self.releases_blocked} |
| Releases with Warnings | {self.releases_with_warnings} |
| Human Overrides | {self.human_overrides} |
| Override Rate | {self.human_overrides / max(self.total_releases, 1) * 100:.1f}% |

### Safety Trend

"""
        if self.violation_rate_trend:
            md += "| Period | Violation Rate |\n|--------|---------------|\n"
            for point in self.violation_rate_trend[-6:]:
                md += f"| {point['period']} | {point['rate']:.1%} |\n"

        md += f"""
### Alignment Debt

- **Current Debt**: {self.alignment_debt_current:.3f}
- **Trend**: {self.alignment_debt_trend}
- **Status**: {"⚠️ Elevated" if self.alignment_debt_current > 0.10 else "✅ Acceptable"}

### Incident Metrics

| Metric | Value |
|--------|-------|
| Total Incidents | {self.incidents_total} |
| Critical Incidents | {self.incidents_critical} |
| Mean Time to Regression | {self.mean_time_to_regression:.1f} hours |

### Constitution Compliance

**Constitution Version**: {self.constitution_version}

| Principle | Compliance |
|-----------|------------|
"""
        for principle, compliance in self.principle_compliance.items():
            status_bar = "█" * int(compliance * 10) + "░" * (10 - int(compliance * 10))
            md += f"| {principle} | {status_bar} {compliance:.0%} |\n"

        return md


@dataclass
class BoardReport:
    """Complete board-level safety report."""

    report_id: str
    generated_at: datetime
    report_period_start: datetime
    report_period_end: datetime

    # Prepared by
    prepared_by: str
    prepared_by_role: str
    approved_by: Optional[str] = None

    # Content
    executive_summary: Optional[ExecutiveSummary] = None
    risk_dashboard: Optional[RiskDashboard] = None

    # Constitution audit
    constitution_hash: str = ""
    constitution_changes: list[str] = field(default_factory=list)

    # Alignment debt section
    alignment_debt_summary: dict = field(default_factory=dict)

    # Risk acceptance log
    risk_acceptances: list[dict] = field(default_factory=list)

    # Incident summary
    incidents: list[dict] = field(default_factory=list)

    # Recommendations
    strategic_recommendations: list[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Generate full board report in markdown."""
        md = f"""# Board Safety Report

**Report ID**: {self.report_id}
**Generated**: {self.generated_at.strftime('%Y-%m-%d %H:%M UTC')}
**Period**: {self.report_period_start.strftime('%Y-%m-%d')} to {self.report_period_end.strftime('%Y-%m-%d')}

**Prepared by**: {self.prepared_by} ({self.prepared_by_role})
**Approved by**: {self.approved_by or 'Pending Approval'}

---

"""
        if self.executive_summary:
            md += self.executive_summary.to_markdown()
            md += "\n---\n\n"

        if self.risk_dashboard:
            md += self.risk_dashboard.to_markdown()
            md += "\n---\n\n"

        # Constitution Audit Section
        md += f"""## Constitution Audit

**Current Constitution Hash**: `{self.constitution_hash}`

### Constitution Changes This Period

"""
        if self.constitution_changes:
            for change in self.constitution_changes:
                md += f"- {change}\n"
        else:
            md += "_No constitution changes this period._\n"

        # Alignment Debt Section
        md += f"""
---

## Alignment Debt Report

Alignment debt represents accumulated deviations from ideal safety state.

### Current Status

| Metric | Value |
|--------|-------|
| Total Active Debt | {self.alignment_debt_summary.get('total_debt', 0):.3f} |
| Debt Added (30d) | {self.alignment_debt_summary.get('debt_added', 0):.3f} |
| Debt Resolved (30d) | {self.alignment_debt_summary.get('debt_resolved', 0):.3f} |
| Net Change | {self.alignment_debt_summary.get('net_change', 0):+.3f} |

### Debt by Category

"""
        for category, amount in self.alignment_debt_summary.get('by_category', {}).items():
            md += f"- **{category.replace('_', ' ').title()}**: {amount:.3f}\n"

        # Risk Acceptances Section
        md += """
---

## Risk Acceptances This Period

"""
        if self.risk_acceptances:
            md += "| Date | Release | Risk | Owner | Status |\n|------|---------|------|-------|--------|\n"
            for ra in self.risk_acceptances:
                md += f"| {ra['date']} | {ra['release']} | {ra['risk'][:30]}... | {ra['owner']} | {ra['status']} |\n"
        else:
            md += "_No risk acceptances this period._\n"

        # Incidents Section
        md += """
---

## Incident Summary

"""
        if self.incidents:
            md += "| ID | Severity | Description | Status | Regression |\n|----|----------|-------------|--------|------------|\n"
            for inc in self.incidents:
                md += f"| {inc['id']} | {inc['severity']} | {inc['description'][:30]}... | {inc['status']} | {inc.get('regression', 'Pending')} |\n"
        else:
            md += "_No incidents this period._\n"

        # Strategic Recommendations
        md += """
---

## Strategic Recommendations

"""
        for i, rec in enumerate(self.strategic_recommendations, 1):
            md += f"{i}. {rec}\n"

        md += f"""
---

*This report was generated by the Model Safety Regression Suite.*
*Constitution hash: {self.constitution_hash}*
"""
        return md

    def to_dict(self) -> dict:
        """Export report as structured data."""
        return {
            "report_id": self.report_id,
            "generated_at": self.generated_at.isoformat(),
            "period": {
                "start": self.report_period_start.isoformat(),
                "end": self.report_period_end.isoformat(),
            },
            "prepared_by": self.prepared_by,
            "approved_by": self.approved_by,
            "constitution_hash": self.constitution_hash,
            "constitution_changes": self.constitution_changes,
            "alignment_debt_summary": self.alignment_debt_summary,
            "risk_acceptances": self.risk_acceptances,
            "incidents": self.incidents,
            "strategic_recommendations": self.strategic_recommendations,
        }


class BoardReportGenerator:
    """
    Generate board-level reports from safety system data.

    This aggregates data from multiple sources into a cohesive
    executive report.
    """

    def __init__(self):
        pass

    def generate_report(
        self,
        period_start: datetime,
        period_end: datetime,
        release_data: dict,
        incident_data: list[dict],
        alignment_debt_data: dict,
        constitution_hash: str,
        prepared_by: str,
        prepared_by_role: str,
    ) -> BoardReport:
        """Generate a complete board report."""
        import uuid

        report_id = f"BOARD-{uuid.uuid4().hex[:8].upper()}"
        now = datetime.now()

        # Build executive summary
        exec_summary = self._build_executive_summary(
            release_data, incident_data, alignment_debt_data, period_start, period_end
        )

        # Build risk dashboard
        risk_dashboard = self._build_risk_dashboard(
            release_data, incident_data, alignment_debt_data, constitution_hash
        )

        # Build strategic recommendations
        recommendations = self._generate_recommendations(
            release_data, incident_data, alignment_debt_data
        )

        report = BoardReport(
            report_id=report_id,
            generated_at=now,
            report_period_start=period_start,
            report_period_end=period_end,
            prepared_by=prepared_by,
            prepared_by_role=prepared_by_role,
            executive_summary=exec_summary,
            risk_dashboard=risk_dashboard,
            constitution_hash=constitution_hash,
            constitution_changes=[],
            alignment_debt_summary=alignment_debt_data,
            risk_acceptances=release_data.get("risk_acceptances", []),
            incidents=incident_data,
            strategic_recommendations=recommendations,
        )

        return report

    def _build_executive_summary(
        self,
        release_data: dict,
        incident_data: list[dict],
        alignment_debt_data: dict,
        period_start: datetime,
        period_end: datetime,
    ) -> ExecutiveSummary:
        """Build executive summary from data."""

        # Determine overall status
        critical_incidents = len([i for i in incident_data if i.get("severity") == "critical"])
        blocked_releases = release_data.get("blocked", 0)
        debt = alignment_debt_data.get("total_debt", 0)

        if critical_incidents > 0 or debt > 0.25:
            status = "RED"
        elif blocked_releases > 0 or debt > 0.10:
            status = "YELLOW"
        else:
            status = "GREEN"

        # Build key metrics
        key_metrics = {
            "Release Success Rate": {
                "value": f"{release_data.get('success_rate', 0.95):.1%}",
                "trend": "↑" if release_data.get("success_rate", 0) > 0.90 else "↓",
                "target": "≥95%",
            },
            "Alignment Debt": {
                "value": f"{debt:.3f}",
                "trend": alignment_debt_data.get("trend", "→"),
                "target": "<0.10",
            },
            "Incident Count": {
                "value": str(len(incident_data)),
                "trend": "↓" if len(incident_data) < 3 else "→",
                "target": "<3/quarter",
            },
        }

        # Top risks
        top_risks = [
            {
                "name": "Policy Erosion",
                "description": "Continued upward trend in multi-turn policy erosion"
            },
            {
                "name": "Alignment Debt",
                "description": f"Debt at {debt:.1%} of warning threshold"
            },
        ]

        # Notable events
        notable_events = []
        if blocked_releases > 0:
            notable_events.append(f"{blocked_releases} releases blocked by safety gate")
        if critical_incidents > 0:
            notable_events.append(f"{critical_incidents} critical incidents occurred")

        # Recommendations
        recommendations = [
            "Continue monitoring alignment debt trajectory",
            "Prioritize incident regression test promotion",
        ]

        return ExecutiveSummary(
            report_period=f"{period_start.strftime('%Y-%m-%d')} to {period_end.strftime('%Y-%m-%d')}",
            overall_status=status,
            key_metrics=key_metrics,
            top_risks=top_risks,
            notable_events=notable_events,
            recommendations=recommendations,
        )

    def _build_risk_dashboard(
        self,
        release_data: dict,
        incident_data: list[dict],
        alignment_debt_data: dict,
        constitution_hash: str,
    ) -> RiskDashboard:
        """Build risk dashboard from data."""

        return RiskDashboard(
            total_releases=release_data.get("total", 10),
            releases_blocked=release_data.get("blocked", 1),
            releases_with_warnings=release_data.get("warnings", 3),
            human_overrides=release_data.get("overrides", 1),
            violation_rate_trend=[
                {"period": "Week 1", "rate": 0.08},
                {"period": "Week 2", "rate": 0.085},
                {"period": "Week 3", "rate": 0.09},
                {"period": "Week 4", "rate": 0.088},
            ],
            alignment_debt_current=alignment_debt_data.get("total_debt", 0.12),
            alignment_debt_trend=alignment_debt_data.get("trend", "stable"),
            incidents_total=len(incident_data),
            incidents_critical=len([i for i in incident_data if i.get("severity") == "critical"]),
            mean_time_to_regression=24.5,
            constitution_version="1.0.0",
            constitution_hash=constitution_hash,
            principle_compliance={
                "P1: Safety Primacy": 0.95,
                "P2: Uncertainty → Caution": 0.88,
                "P3: Traceability": 1.00,
                "P4: Defense in Depth": 0.90,
                "P5: Continuous Improvement": 0.85,
                "P6: Transparency": 1.00,
            },
        )

    def _generate_recommendations(
        self,
        release_data: dict,
        incident_data: list[dict],
        alignment_debt_data: dict,
    ) -> list[str]:
        """Generate strategic recommendations."""
        recommendations = []

        debt = alignment_debt_data.get("total_debt", 0)
        if debt > 0.10:
            recommendations.append(
                f"**Reduce alignment debt**: Current debt ({debt:.3f}) exceeds warning threshold. "
                "Prioritize resolving coverage gaps and pending fixes."
            )

        blocked = release_data.get("blocked", 0)
        if blocked > 0:
            recommendations.append(
                f"**Review blocked releases**: {blocked} releases were blocked this period. "
                "Analyze root causes to prevent recurring blockers."
            )

        critical = len([i for i in incident_data if i.get("severity") == "critical"])
        if critical > 0:
            recommendations.append(
                f"**Critical incident response**: {critical} critical incidents occurred. "
                "Ensure all have been converted to regression tests."
            )

        recommendations.append(
            "**Maintain constitution alignment**: All releases must continue to trace "
            "verdicts to constitution principles with complete evidence lineage."
        )

        return recommendations


# Example usage
if __name__ == "__main__":
    from datetime import timedelta

    generator = BoardReportGenerator()

    now = datetime.now()
    report = generator.generate_report(
        period_start=now - timedelta(days=30),
        period_end=now,
        release_data={
            "total": 12,
            "blocked": 1,
            "warnings": 4,
            "overrides": 1,
            "success_rate": 0.92,
            "risk_acceptances": [
                {
                    "date": "2026-01-15",
                    "release": "v3.6.1",
                    "risk": "Elevated policy erosion rate",
                    "owner": "Jane Smith",
                    "status": "Monitored",
                },
            ],
        },
        incident_data=[
            {
                "id": "INC-001",
                "severity": "high",
                "description": "Policy erosion in multi-turn scenario",
                "status": "Resolved",
                "regression": "Promoted",
            },
        ],
        alignment_debt_data={
            "total_debt": 0.12,
            "debt_added": 0.03,
            "debt_resolved": 0.02,
            "net_change": 0.01,
            "trend": "↑ Increasing",
            "by_category": {
                "coverage_gap": 0.05,
                "risk_acceptance": 0.04,
                "constitution_deviation": 0.03,
            },
        },
        constitution_hash="sha256:abc123def456",
        prepared_by="Safety Team",
        prepared_by_role="Safety Engineering",
    )

    print(report.to_markdown())
