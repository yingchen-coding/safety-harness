#!/usr/bin/env python3
"""
Generate Unified Executive Safety Dashboard

Single-page HTML dashboard combining:
- Board Brief (release block status)
- Exception Audit (governance risk)
- Investment Recommendation (resource allocation)
- ROI Model (financial framing)

This is the board-meeting-ready artifact.

Usage:
    python scripts/generate_executive_dashboard.py
    python scripts/generate_executive_dashboard.py --output artifacts/executive_safety_dashboard.html
"""

import yaml
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "artifacts" / "gate_report.json"
DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
EXCEPTIONS_PATH = ROOT / "artifacts" / "safety_exceptions.yaml"
ROI_PATH = ROOT / "artifacts" / "safety_roi_model.json"
PORTFOLIO_PATH = ROOT / "artifacts" / "safety_portfolio_plan.json"
ROI_CURVE_PATH = ROOT / "artifacts" / "roi_curve.json"
HEATMAP_PATH = ROOT / "artifacts" / "risk_heatmap.json"
OUTPUT_PATH = ROOT / "artifacts" / "executive_safety_dashboard.html"


def load_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def generate_dashboard() -> str:
    """Generate unified executive dashboard HTML."""
    timestamp = datetime.now(timezone.utc).isoformat()

    # Load all data sources
    gate = load_json(GATE_PATH)
    debt_data = load_yaml(DEBT_PATH)
    exc_data = load_yaml(EXCEPTIONS_PATH)
    roi = load_json(ROI_PATH)
    portfolio = load_json(PORTFOLIO_PATH)
    roi_curve = load_json(ROI_CURVE_PATH) if ROI_CURVE_PATH.exists() else []
    heatmap = load_json(HEATMAP_PATH)

    debts = debt_data.get("ledger", debt_data.get("debts", []))
    exceptions = exc_data.get("exceptions", [])

    # Extract key metrics
    verdict = gate.get("verdict", "UNKNOWN")
    release = gate.get("release_candidate", "N/A")
    primary_risk = gate.get("summary", {}).get("primary_risk", "No data")

    open_debts = [d for d in debts if d.get("status") == "open" or d.get("mitigation_status") == "open"]
    critical_debts = [d for d in open_debts if d.get("severity") == "critical"]
    active_exceptions = [e for e in exceptions if e.get("status") == "active"]

    # ROI metrics
    prob = roi.get("probability_analysis", {}).get("total_probability", 0)
    expected_cost = roi.get("cost_analysis", {}).get("annualized_expected_cost", 0)
    roi.get("investment_analysis", {}).get("optimal_investment", {})
    headline = roi.get("board_headline", "ROI data not available")

    # Verdict styling
    verdict_colors = {
        "OK": {"bg": "#28a745", "text": "white"},
        "WARN": {"bg": "#ffc107", "text": "#1a1a2e"},
        "BLOCK": {"bg": "#dc3545", "text": "white"},
        "UNKNOWN": {"bg": "#6c757d", "text": "white"}
    }
    vc = verdict_colors.get(verdict, verdict_colors["UNKNOWN"])

    # Risk level
    if prob > 0.15:
        risk_color = "#dc3545"
    elif prob > 0.08:
        risk_color = "#fd7e14"
    elif prob > 0.04:
        risk_color = "#ffc107"
    else:
        risk_color = "#28a745"

    # Generate debt cards
    debt_cards = ""
    for d in open_debts[:4]:
        sev = d.get("severity", "medium")
        sev_color = {"critical": "#dc3545", "high": "#fd7e14", "medium": "#ffc107"}.get(sev, "#6c757d")
        debt_cards += f"""
        <div class="mini-card">
            <div style="font-weight: bold; color: {sev_color};">{d.get('debt_id', 'Unknown')}</div>
            <div style="font-size: 12px; color: #94a3b8;">
                {d.get('principle', '?')} | {d.get('age_days', 0)}d old
            </div>
        </div>
        """

    if not debt_cards:
        debt_cards = "<p style='color: #28a745;'>No open alignment debt</p>"

    # Generate exception cards
    exc_cards = ""
    for e in active_exceptions[:3]:
        ttl = e.get("ttl_remaining_days", 0)
        ttl_color = "#dc3545" if ttl <= 3 else ("#ffc107" if ttl <= 7 else "#28a745")
        exc_cards += f"""
        <div class="mini-card">
            <div style="font-weight: bold;">{e.get('exception_id', 'Unknown')}</div>
            <div style="font-size: 12px;">
                <span style="color: {ttl_color};">TTL: {ttl}d</span> |
                Renewals: {e.get('renewal_count', 0)}/{e.get('max_renewals', 2)}
            </div>
        </div>
        """

    if not exc_cards:
        exc_cards = "<p style='color: #28a745;'>No active exceptions</p>"

    # ROI scenarios
    roi_rows = ""
    for s in roi.get("investment_analysis", {}).get("scenarios", [])[:4]:
        benefit_color = "#28a745" if s.get("net_benefit", 0) > 0 else "#dc3545"
        roi_rows += f"""
        <tr>
            <td>{s.get('fte_added', 0)} FTE</td>
            <td>${s.get('investment', 0):,.0f}</td>
            <td>{s.get('probability_reduction', 0)*100:.1f}%</td>
            <td style="color: {benefit_color};">${s.get('net_benefit', 0):,.0f}</td>
            <td>{s.get('roi_percent', 0):.0f}%</td>
        </tr>
        """

    # Portfolio recommendations
    portfolio_cards = ""
    for i, p in enumerate(portfolio.get("portfolio", [])[:3], 1):
        portfolio_cards += f"""
        <div class="portfolio-card">
            <div class="portfolio-rank">#{i}</div>
            <div class="portfolio-details">
                <div class="portfolio-name">{p.get('safeguard', 'Unknown')}</div>
                <div class="portfolio-meta">
                    ${p.get('allocated_usd', 0):,} → <strong>-{p.get('expected_risk_reduction_pct', 0)}%</strong> risk
                </div>
                <div class="portfolio-tags">
                    <span class="tag">{p.get('blast_radius', '?')} blast</span>
                    <span class="tag">{p.get('maturity', '?')} maturity</span>
                </div>
            </div>
        </div>
        """

    total_portfolio_reduction = portfolio.get("total_expected_risk_reduction_pct", 0)
    portfolio_budget = portfolio.get("budget_usd", 0)

    # ROI curve points
    roi_curve_points = ""
    for point in roi_curve[:6]:
        roi_curve_points += f"""
        <div class="curve-point">
            <div class="curve-investment">${point.get('investment_usd', 0):,}</div>
            <div class="curve-reduction">-{point.get('risk_reduction_pct', 0)}%</div>
        </div>
        """

    # Risk heatmap
    heatmap_items = ""
    vectors = heatmap.get("vectors", {})
    level_colors = {
        "critical": "#dc3545",
        "high": "#fd7e14",
        "medium": "#ffc107",
        "low": "#28a745"
    }
    for vector, level in vectors.items():
        color = level_colors.get(level, "#6c757d")
        heatmap_items += f"""
        <div class="heatmap-item">
            <span class="heatmap-vector">{vector.replace('_', ' ').title()}</span>
            <span class="heatmap-level" style="background: {color};">{level.upper()}</span>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Executive Safety Dashboard</title>
    <style>
        * {{ box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #16213e 100%);
            color: #e2e8f0;
            margin: 0;
            padding: 20px;
            min-height: 100vh;
        }}
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 2px solid rgba(255,255,255,0.1);
            margin-bottom: 30px;
        }}
        .header h1 {{
            font-size: 36px;
            margin: 0;
            background: linear-gradient(90deg, #ffc107, #fd7e14, #dc3545);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header .meta {{
            color: #94a3b8;
            font-size: 14px;
            margin-top: 10px;
        }}
        .verdict-banner {{
            background: {vc['bg']};
            color: {vc['text']};
            padding: 25px;
            border-radius: 12px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        .verdict-banner h2 {{
            font-size: 48px;
            margin: 0;
        }}
        .verdict-banner p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
        }}
        .grid {{
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 20px;
            margin-bottom: 30px;
        }}
        .metric-card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }}
        .metric-card .number {{
            font-size: 42px;
            font-weight: bold;
        }}
        .metric-card .label {{
            color: #94a3b8;
            font-size: 12px;
            text-transform: uppercase;
            margin-top: 5px;
        }}
        .section-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 30px;
        }}
        .section {{
            background: rgba(255,255,255,0.03);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 20px;
        }}
        .section h3 {{
            margin: 0 0 15px 0;
            color: #ffc107;
            font-size: 16px;
            text-transform: uppercase;
        }}
        .mini-card {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            margin: 8px 0;
        }}
        .roi-highlight {{
            background: linear-gradient(135deg, rgba(255,193,7,0.2), rgba(253,126,20,0.2));
            border: 2px solid #ffc107;
            border-radius: 12px;
            padding: 25px;
            text-align: center;
            margin-bottom: 30px;
        }}
        .roi-highlight h3 {{
            color: #ffc107;
            margin: 0 0 10px 0;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .roi-highlight .headline {{
            font-size: 20px;
            font-weight: bold;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }}
        th, td {{
            padding: 10px;
            text-align: left;
            border-bottom: 1px solid rgba(255,255,255,0.1);
        }}
        th {{
            color: #94a3b8;
            font-weight: normal;
            text-transform: uppercase;
            font-size: 11px;
        }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #6c757d;
            font-size: 12px;
        }}
        .portfolio-card {{
            display: flex;
            align-items: center;
            background: rgba(0,0,0,0.2);
            padding: 15px;
            border-radius: 8px;
            margin: 10px 0;
            border-left: 4px solid #ffc107;
        }}
        .portfolio-rank {{
            font-size: 24px;
            font-weight: bold;
            color: #ffc107;
            margin-right: 15px;
            min-width: 40px;
        }}
        .portfolio-details {{
            flex: 1;
        }}
        .portfolio-name {{
            font-weight: bold;
            font-size: 14px;
            margin-bottom: 5px;
        }}
        .portfolio-meta {{
            font-size: 13px;
            color: #94a3b8;
        }}
        .portfolio-tags {{
            margin-top: 8px;
        }}
        .tag {{
            display: inline-block;
            background: rgba(255,255,255,0.1);
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
            margin-right: 5px;
        }}
        .curve-container {{
            display: flex;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 10px;
        }}
        .curve-point {{
            background: rgba(0,0,0,0.2);
            padding: 12px;
            border-radius: 8px;
            text-align: center;
            flex: 1;
            min-width: 80px;
        }}
        .curve-investment {{
            font-size: 12px;
            color: #94a3b8;
        }}
        .curve-reduction {{
            font-size: 18px;
            font-weight: bold;
            color: #28a745;
        }}
        .heatmap-grid {{
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 8px;
        }}
        .heatmap-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            background: rgba(0,0,0,0.2);
            padding: 10px 12px;
            border-radius: 6px;
        }}
        .heatmap-vector {{
            font-size: 13px;
        }}
        .heatmap-level {{
            padding: 3px 10px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
            color: white;
        }}
        .portfolio-summary {{
            background: linear-gradient(135deg, rgba(40,167,69,0.2), rgba(255,193,7,0.2));
            border: 2px solid #28a745;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            margin-top: 15px;
        }}
        .portfolio-summary .headline {{
            font-size: 18px;
            font-weight: bold;
        }}
        @media print {{
            body {{ background: white; color: black; }}
            .metric-card, .section {{ border: 1px solid #ddd; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Executive Safety Dashboard</h1>
            <div class="meta">
                Release: <strong>{release}</strong> | Generated: {timestamp} | Classification: Internal - Board Level
            </div>
        </div>

        <div class="verdict-banner">
            <h2>{verdict}</h2>
            <p>{primary_risk}</p>
        </div>

        <div class="grid">
            <div class="metric-card">
                <div class="number" style="color: {risk_color};">{prob*100:.1f}%</div>
                <div class="label">Incident Probability</div>
            </div>
            <div class="metric-card">
                <div class="number" style="color: #fd7e14;">{len(open_debts)}</div>
                <div class="label">Open Alignment Debt</div>
            </div>
            <div class="metric-card">
                <div class="number" style="color: #ffc107;">{len(active_exceptions)}</div>
                <div class="label">Active Exceptions</div>
            </div>
            <div class="metric-card">
                <div class="number" style="color: #dc3545;">${expected_cost/1000000:.1f}M</div>
                <div class="label">Annual Risk Exposure</div>
            </div>
        </div>

        <div class="roi-highlight">
            <h3>💰 Board-Level Investment Recommendation</h3>
            <div class="headline">{headline}</div>
        </div>

        <div class="section-grid">
            <div class="section">
                <h3>📋 Alignment Debt ({len(open_debts)} open, {len(critical_debts)} critical)</h3>
                {debt_cards}
            </div>
            <div class="section">
                <h3>🔒 Active Exceptions ({len(active_exceptions)})</h3>
                {exc_cards}
            </div>
        </div>

        <div class="section">
            <h3>📊 Investment Scenarios</h3>
            <table>
                <thead>
                    <tr>
                        <th>Investment</th>
                        <th>Cost</th>
                        <th>Risk Reduction</th>
                        <th>Net Benefit</th>
                        <th>ROI</th>
                    </tr>
                </thead>
                <tbody>
                    {roi_rows}
                </tbody>
            </table>
        </div>

        <div class="section-grid">
            <div class="section">
                <h3>🎯 Recommended Portfolio (Top-3 Safeguards)</h3>
                {portfolio_cards if portfolio_cards else "<p style='color: #6c757d;'>Run portfolio optimizer first</p>"}
                <div class="portfolio-summary">
                    <div class="headline">
                        ${portfolio_budget:,} investment → -{total_portfolio_reduction}% total risk reduction
                    </div>
                </div>
            </div>
            <div class="section">
                <h3>🔥 Risk Heatmap (Current Quarter)</h3>
                <div class="heatmap-grid">
                    {heatmap_items if heatmap_items else "<p style='color: #6c757d;'>No heatmap data</p>"}
                </div>
            </div>
        </div>

        <div class="section">
            <h3>📈 Safety ROI Curve (Diminishing Returns)</h3>
            <div class="curve-container">
                {roi_curve_points if roi_curve_points else "<p style='color: #6c757d;'>No ROI curve data</p>"}
            </div>
            <p style="margin-top: 15px; font-size: 13px; color: #94a3b8; text-align: center;">
                Investment shows diminishing returns beyond $500k. Optimal allocation follows portfolio recommendation above.
            </p>
        </div>

        <div class="footer">
            <p>Generated by Model Safety Regression Suite | Constitution-as-Code Governance</p>
            <p>This dashboard provides board-level visibility into AI safety posture and investment recommendations.</p>
        </div>
    </div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate Unified Executive Safety Dashboard"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output HTML path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("EXECUTIVE SAFETY DASHBOARD GENERATOR")
    print("=" * 60)

    import subprocess

    # Generate prerequisites if they don't exist
    roi_path = ROOT / "artifacts" / "safety_roi_model.json"
    if not roi_path.exists():
        print("\n[INFO] Generating ROI model...")
        subprocess.run(["python", str(ROOT / "scripts" / "generate_safety_roi_model.py")])

    portfolio_path = ROOT / "artifacts" / "safety_portfolio_plan.json"
    if not portfolio_path.exists():
        print("[INFO] Generating portfolio plan...")
        subprocess.run(["python", str(ROOT / "scripts" / "optimize_safety_portfolio.py")])

    heatmap_path = ROOT / "artifacts" / "risk_heatmap.json"
    if not heatmap_path.exists():
        print("[INFO] Generating ROI curve and heatmap...")
        subprocess.run(["python", str(ROOT / "scripts" / "gen_roi_curve_and_heatmap.py")])

    html = generate_dashboard()

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)

    print(f"\n[OK] Executive dashboard generated: {args.output}")
    print("[OK] This is your board-meeting-ready artifact")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
