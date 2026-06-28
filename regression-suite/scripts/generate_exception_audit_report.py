#!/usr/bin/env python3
"""
Generate CEO/Board Safety Exception Audit Report

When exception budget is exceeded or exceptions accumulate,
generates an audit report for executive oversight.

Usage:
    python scripts/generate_exception_audit_report.py
    python scripts/generate_exception_audit_report.py --output artifacts/ceo_board_exception_audit.html
"""

import yaml
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
EXCEPTIONS_PATH = ROOT / "artifacts" / "safety_exceptions.yaml"
BUDGET_PATH = ROOT / "config" / "alignment_error_budget.yaml"
OUTPUT_PATH = ROOT / "artifacts" / "ceo_board_exception_audit.html"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def calculate_governance_risk(exceptions: list, budget_config: dict) -> dict:
    """Calculate governance risk metrics."""
    active = [e for e in exceptions if e.get("status") == "active"]
    total_safeguards_covered = sum(e.get("safeguards_covered", 0) for e in active)
    total_renewals = sum(e.get("renewal_count", 0) for e in active)

    max_budget = budget_config.get("error_budget", {}).get("max_new_alignment_debts", 2)
    budget_exceeded = len(active) > max_budget

    # Risk indicators
    risk_level = "LOW"
    risk_factors = []

    if budget_exceeded:
        risk_level = "HIGH"
        risk_factors.append("Exception budget exceeded")

    if total_renewals > 2:
        risk_level = "HIGH" if risk_level != "HIGH" else "CRITICAL"
        risk_factors.append("Multiple exception renewals indicate systemic issues")

    if total_safeguards_covered > 5:
        risk_level = "MEDIUM" if risk_level == "LOW" else risk_level
        risk_factors.append("Large safeguard coverage increases attack surface")

    # Check for near-expiry exceptions
    near_expiry = [e for e in active if e.get("ttl_remaining_days", 30) <= 3]
    if near_expiry:
        risk_factors.append(f"{len(near_expiry)} exception(s) expiring within 3 days")

    return {
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "budget_exceeded": budget_exceeded,
        "active_count": len(active),
        "total_safeguards_covered": total_safeguards_covered,
        "total_renewals": total_renewals
    }


def generate_audit_report(exceptions: list, budget_config: dict) -> str:
    """Generate CEO/Board audit HTML report."""
    timestamp = datetime.now(timezone.utc).isoformat()
    active = [e for e in exceptions if e.get("status") == "active"]
    risk = calculate_governance_risk(exceptions, budget_config)

    risk_colors = {
        "LOW": "#28a745",
        "MEDIUM": "#ffc107",
        "HIGH": "#fd7e14",
        "CRITICAL": "#dc3545"
    }
    risk_color = risk_colors.get(risk["risk_level"], "#6c757d")

    # Generate exception cards
    exception_cards = ""
    for e in active:
        ttl = e.get("ttl_remaining_days", 0)
        ttl_color = "#dc3545" if ttl <= 3 else ("#ffc107" if ttl <= 7 else "#28a745")

        exception_cards += f"""
        <div class="exception-card">
            <div class="exception-header">
                <strong>{e.get('exception_id', 'Unknown')}</strong>
                <span class="status-badge">ACTIVE</span>
            </div>
            <div class="exception-body">
                <div><strong>Repository:</strong> {e.get('repo_scope', e.get('repo', 'Unknown'))}</div>
                <div><strong>Approved By:</strong> {e.get('approved_by', 'Unknown')}</div>
                <div><strong>Safeguards Covered:</strong> {e.get('safeguards_covered', 0)}</div>
                <div><strong>Principles:</strong> {', '.join(e.get('constitution_principles', e.get('safeguard_scope', {}).get('constitution_principles', [])))}</div>
                <div><strong>Renewals:</strong> {e.get('renewal_count', 0)} / {e.get('max_renewals', 2)}</div>
                <div style="color: {ttl_color};"><strong>TTL:</strong> {ttl} days remaining</div>
                <div><strong>Expires:</strong> {e.get('expires_at', 'Unknown')}</div>
                <div class="justification"><strong>Justification:</strong> {e.get('justification', 'Not provided')}</div>
            </div>
        </div>
        """

    if not exception_cards:
        exception_cards = "<p class='no-data'>No active exceptions</p>"

    # Generate risk factors list
    risk_factors_html = ""
    for factor in risk["risk_factors"]:
        risk_factors_html += f"<li>{factor}</li>"
    if not risk_factors_html:
        risk_factors_html = "<li>No significant risk factors identified</li>"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>CEO/Board Safety Exception Audit</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 20px;
            color: #1a1a2e;
            line-height: 1.6;
        }}
        .header {{
            border-bottom: 3px solid #16213e;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #16213e;
            margin: 0;
        }}
        .meta {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 10px;
        }}
        .risk-banner {{
            background: {risk_color};
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin: 20px 0;
            text-align: center;
        }}
        .risk-banner h2 {{
            margin: 0;
            font-size: 28px;
        }}
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin: 20px 0;
        }}
        .summary-card {{
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }}
        .summary-card .number {{
            font-size: 36px;
            font-weight: bold;
            color: #16213e;
        }}
        .summary-card .label {{
            color: #6c757d;
            font-size: 14px;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #16213e;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }}
        .exception-card {{
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            margin: 15px 0;
            overflow: hidden;
        }}
        .exception-header {{
            background: #16213e;
            color: white;
            padding: 12px 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .status-badge {{
            background: #ffc107;
            color: #1a1a2e;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }}
        .exception-body {{
            padding: 15px;
            background: white;
        }}
        .exception-body div {{
            margin: 8px 0;
        }}
        .justification {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            margin-top: 10px !important;
        }}
        .risk-factors {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
        }}
        .risk-factors ul {{
            margin: 10px 0;
            padding-left: 20px;
        }}
        .governance-warning {{
            background: #f8d7da;
            border: 1px solid #dc3545;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
        }}
        .no-data {{
            color: #6c757d;
            font-style: italic;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #e2e8f0;
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 CEO / Board Safety Exception Audit</h1>
        <div class="meta">
            <strong>Generated:</strong> {timestamp}<br/>
            <strong>Classification:</strong> Internal - Executive Review<br/>
            <strong>Audit Period:</strong> Current Quarter
        </div>
    </div>

    <div class="risk-banner">
        <h2>Governance Risk: {risk["risk_level"]}</h2>
        <p>{"Exception budget exceeded - immediate review required" if risk["budget_exceeded"] else "Within acceptable governance thresholds"}</p>
    </div>

    <div class="summary-grid">
        <div class="summary-card">
            <div class="number">{risk["active_count"]}</div>
            <div class="label">Active Exceptions</div>
        </div>
        <div class="summary-card">
            <div class="number">{risk["total_safeguards_covered"]}</div>
            <div class="label">Safeguards Covered</div>
        </div>
        <div class="summary-card">
            <div class="number">{risk["total_renewals"]}</div>
            <div class="label">Total Renewals</div>
        </div>
    </div>

    <div class="section">
        <h2>Risk Factors</h2>
        <div class="risk-factors">
            <ul>
                {risk_factors_html}
            </ul>
        </div>
    </div>

    {"<div class='governance-warning'><strong>⚠️ Governance Warning</strong><p>Exception budget exceeded. This indicates potential normalization of deviance - a pattern where safety controls are routinely bypassed. Board-level review recommended.</p></div>" if risk["budget_exceeded"] else ""}

    <div class="section">
        <h2>Active Exceptions Detail</h2>
        {exception_cards}
    </div>

    <div class="section">
        <h2>Recommendations</h2>
        <ol>
            <li>Review each active exception for continued necessity</li>
            <li>Prioritize remediation of underlying issues to reduce exception count</li>
            <li>Consider increasing safety engineering capacity if exceptions are chronic</li>
            <li>Schedule quarterly exception review with Safety Director</li>
        </ol>
    </div>

    <div class="footer">
        <p>Generated by Model Safety Regression Suite | Constitution-as-Code Governance</p>
        <p>This audit report provides executive visibility into safety exception patterns.</p>
    </div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate CEO/Board Safety Exception Audit Report"
    )
    parser.add_argument(
        "--exceptions", "-e",
        type=Path,
        default=EXCEPTIONS_PATH,
        help="Path to safety_exceptions.yaml"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output HTML path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("CEO/BOARD EXCEPTION AUDIT GENERATOR")
    print("=" * 60)

    data = load_yaml(args.exceptions)
    exceptions = data.get("exceptions", [])
    budget_config = load_yaml(BUDGET_PATH)

    html = generate_audit_report(exceptions, budget_config)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)

    risk = calculate_governance_risk(exceptions, budget_config)

    print(f"\n[OK] CEO/Board exception audit generated: {args.output}")
    print(f"[OK] Active exceptions: {risk['active_count']}")
    print(f"[OK] Governance risk: {risk['risk_level']}")
    print(f"[OK] Budget exceeded: {risk['budget_exceeded']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
