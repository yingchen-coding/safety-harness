#!/usr/bin/env python3
"""
Render Organizational Safety Risk Dashboard

Generates visual HTML dashboard from risk_ledger.json showing:
- Active exceptions with TTL countdown
- Alignment debt with SLO status
- Error budget utilization
- Constitution audit summary
- Freeze status

Usage:
    python scripts/render_risk_dashboard.py
    python scripts/render_risk_dashboard.py --output artifacts/risk_dashboard.html
"""

import json
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "artifacts" / "risk_ledger.json"
OUTPUT_PATH = ROOT / "artifacts" / "risk_dashboard.html"


def load_risk_ledger(path: Path) -> dict:
    """Load risk ledger data."""
    with open(path) as f:
        return json.load(f)


def render_exception_card(exc: dict) -> str:
    """Render a single exception as HTML card."""
    status_color = "#ffc107" if exc.get("status") == "active" else "#6c757d"
    ttl = exc.get("ttl_remaining_days", 0)
    ttl_color = "#dc3545" if ttl <= 2 else ("#ffc107" if ttl <= 5 else "#28a745")

    return f"""
    <div style="border: 1px solid {status_color}; padding: 12px; margin: 8px 0; border-radius: 4px; background: rgba(255,193,7,0.1);">
        <strong style="color: {status_color};">⚠️ {exc.get('exception_id')}</strong>
        <div style="margin-top: 8px; font-size: 14px;">
            <div>Approved by: {exc.get('approved_by', 'Unknown')}</div>
            <div>Repo: <code>{exc.get('repo', 'Unknown')}</code></div>
            <div>Principles: {', '.join(exc.get('constitution_principles', []))}</div>
            <div>Safeguards covered: {exc.get('safeguards_covered', 0)}</div>
            <div>Entropy: {exc.get('entropy_score', 0)}/{exc.get('max_entropy', 10)}</div>
            <div>Renewals: {exc.get('renewal_count', 0)}/{exc.get('max_renewals', 2)}</div>
            <div style="color: {ttl_color}; font-weight: bold;">TTL: {ttl} days remaining</div>
        </div>
    </div>
    """


def render_debt_card(debt: dict) -> str:
    """Render a single debt entry as HTML card."""
    severity = debt.get("severity", "medium")
    severity_colors = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#6c757d"
    }
    color = severity_colors.get(severity, "#6c757d")

    slo_breached = debt.get("slo_breached", False)
    status = debt.get("status", "open")
    status_icon = "🔴" if status == "open" else "✅"

    days_until = debt.get("days_until_slo", 0)
    slo_text = f"<span style='color: #dc3545; font-weight: bold;'>SLO BREACHED ({abs(days_until)} days over)</span>" if slo_breached else f"{days_until} days until SLO"

    return f"""
    <div style="border-left: 4px solid {color}; padding: 12px; margin: 8px 0; background: #f8f9fa;">
        <strong>{status_icon} {debt.get('debt_id')}</strong>
        <span style="background: {color}; color: white; padding: 2px 8px; border-radius: 4px; margin-left: 8px; font-size: 12px;">{severity.upper()}</span>
        <div style="margin-top: 8px; font-size: 14px;">
            <div>Principle: <strong>{debt.get('principle')}</strong></div>
            <div>Gap: {debt.get('mechanism_gap', 'Unknown')}</div>
            <div>Age: {debt.get('age_days', 0)} days</div>
            <div>{slo_text}</div>
            {f"<div>Exception: <code>{debt.get('linked_exception')}</code></div>" if debt.get('linked_exception') else ""}
        </div>
    </div>
    """


def render_dashboard(data: dict) -> str:
    """Render complete dashboard HTML."""
    timestamp = data.get("timestamp", datetime.now().isoformat())
    release = data.get("release_candidate", "unknown")

    # Freeze status
    freeze = data.get("freeze_status", {})
    freeze_color = "#dc3545" if freeze.get("frozen") else "#28a745"
    freeze_icon = "🧊" if freeze.get("frozen") else "✅"
    freeze_text = "FROZEN" if freeze.get("frozen") else "ALLOWED"

    # Error budget
    budget = data.get("error_budget", {})
    budget_used = budget.get("budget_used", 0)
    budget_total = budget.get("budget_total", 2)
    budget_pct = min(100, (budget_used / budget_total * 100) if budget_total > 0 else 0)
    budget_color = "#dc3545" if budget.get("exceeded") else ("#ffc107" if budget_pct > 80 else "#28a745")

    # Constitution audit
    audit = data.get("constitution_audit", {})
    violations = audit.get("violations_count", 0)
    high_sev = audit.get("high_severity", 0)
    critical_sev = audit.get("critical_severity", 0)

    # Gate verdict
    verdict = data.get("gate_verdict", {})
    verdict_status = verdict.get("verdict", "UNKNOWN")
    verdict_color = {"OK": "#28a745", "WARN": "#ffc107", "BLOCK": "#dc3545"}.get(verdict_status, "#6c757d")

    # Render exceptions
    exceptions_html = "".join(render_exception_card(e) for e in data.get("exceptions", []))
    if not exceptions_html:
        exceptions_html = "<p style='color: #6c757d;'>No active exceptions</p>"

    # Render debt
    debt_html = "".join(render_debt_card(d) for d in data.get("alignment_debt", []))
    if not debt_html:
        debt_html = "<p style='color: #28a745;'>No alignment debt</p>"

    return f"""<!DOCTYPE html>
<html>
<head>
    <title>Organizational Safety Risk Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #e2e8f0;
            margin: 0;
            padding: 20px;
        }}
        .header {{
            text-align: center;
            padding: 20px;
            border-bottom: 2px solid #333;
            margin-bottom: 20px;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }}
        .card {{
            background: #16213e;
            border-radius: 8px;
            padding: 20px;
        }}
        .card h3 {{
            margin-top: 0;
            color: #94a3b8;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .big-number {{
            font-size: 48px;
            font-weight: bold;
        }}
        .progress-bar {{
            height: 8px;
            background: #333;
            border-radius: 4px;
            overflow: hidden;
            margin-top: 8px;
        }}
        .progress-fill {{
            height: 100%;
            border-radius: 4px;
        }}
        code {{
            background: rgba(0,0,0,0.3);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .verdict-banner {{
            text-align: center;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🛡️ Organizational Safety Risk Dashboard</h1>
        <p>Release: <strong>{release}</strong> | Generated: {timestamp}</p>
    </div>

    <div class="verdict-banner" style="background: rgba({','.join(str(int(verdict_color[i:i+2], 16)) for i in (1, 3, 5))}, 0.2); border: 2px solid {verdict_color};">
        <div class="big-number" style="color: {verdict_color};">{verdict_status}</div>
        <div style="margin-top: 8px;">
            {'; '.join(verdict.get('reasons', ['No reasons provided'])[:3])}
        </div>
    </div>

    <div class="grid">
        <div class="card">
            <h3>🧊 Freeze Status</h3>
            <div class="big-number" style="color: {freeze_color};">{freeze_icon} {freeze_text}</div>
            <div style="margin-top: 8px; font-size: 14px;">{freeze.get('reason', 'No freeze conditions')}</div>
        </div>

        <div class="card">
            <h3>📊 Error Budget (Quarterly)</h3>
            <div class="big-number" style="color: {budget_color};">{budget_used}/{budget_total}</div>
            <div class="progress-bar">
                <div class="progress-fill" style="width: {budget_pct}%; background: {budget_color};"></div>
            </div>
            <div style="margin-top: 8px; font-size: 14px;">{budget.get('quarter', 'Unknown')} | {budget_pct:.0f}% utilized</div>
        </div>

        <div class="card">
            <h3>📜 Constitution Audit</h3>
            <div class="big-number" style="color: {'#dc3545' if critical_sev > 0 else '#ffc107'};">{violations}</div>
            <div style="margin-top: 8px; font-size: 14px;">
                <span style="color: #dc3545;">{critical_sev} critical</span> |
                <span style="color: #fd7e14;">{high_sev} high</span>
            </div>
        </div>
    </div>

    <div class="grid" style="margin-top: 20px;">
        <div class="card">
            <h3>⚠️ Active Exceptions</h3>
            {exceptions_html}
        </div>

        <div class="card">
            <h3>💳 Alignment Debt</h3>
            {debt_html}
        </div>
    </div>

    <footer style="text-align: center; margin-top: 40px; color: #94a3b8; font-size: 12px;">
        <p>Generated by Agentic Safety Demo | Constitution-as-Code Governance System</p>
        <p>Lineage: {data.get('lineage', {}).get('gate_report', 'N/A')}</p>
    </footer>
</body>
</html>"""


def main():
    parser = argparse.ArgumentParser(
        description="Render Organizational Safety Risk Dashboard"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=DATA_PATH,
        help="Path to risk_ledger.json"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output HTML path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("RISK DASHBOARD GENERATOR")
    print("=" * 60)

    data = load_risk_ledger(args.input)
    html = render_dashboard(data)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)

    print(f"\n[OK] Dashboard generated: {args.output}")
    print(f"[OK] Release: {data.get('release_candidate')}")
    print(f"[OK] Verdict: {data.get('gate_verdict', {}).get('verdict', 'UNKNOWN')}")
    print(f"[OK] Freeze: {'FROZEN' if data.get('freeze_status', {}).get('frozen') else 'ALLOWED'}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
