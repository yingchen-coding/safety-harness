#!/usr/bin/env python3
"""
Generate Board Brief - Executive Safety Summary

When a release is BLOCKED, automatically generates a 1-page
board-level summary for executive review.

Usage:
    python scripts/generate_board_brief.py
    python scripts/generate_board_brief.py --output artifacts/board_brief.html
"""

import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
GATE_PATH = ROOT / "artifacts" / "gate_report.json"
OUTPUT_PATH = ROOT / "artifacts" / "board_brief_v1.html"


def load_gate_report(path: Path) -> dict:
    """Load gate report data."""
    if not path.exists():
        return {
            "release_candidate": "unknown",
            "verdict": "BLOCK",
            "summary": {
                "primary_risk": "Safety gate data unavailable",
                "severity": "Unknown",
                "total_regressions": 0,
                "critical_failures": 0
            }
        }
    with open(path) as f:
        return json.load(f)


def generate_board_brief(gate: dict) -> str:
    """Generate board-level HTML brief."""
    timestamp = datetime.now(timezone.utc).isoformat()
    release = gate.get("release_candidate", "unknown")
    verdict = gate.get("verdict", "BLOCK")
    summary = gate.get("summary", {})

    primary_risk = summary.get("primary_risk", "Alignment policy violation detected")
    severity = summary.get("severity", "High")
    total_regressions = summary.get("total_regressions", 0)
    critical_failures = summary.get("critical_failures", 0)

    # Estimate remediation based on severity
    if severity == "critical":
        remediation_window = "4-8 weeks"
        business_impact = "Major feature release frozen, potential quarterly delay"
    elif severity == "high":
        remediation_window = "2-4 weeks"
        business_impact = "Feature release frozen pending safety review"
    else:
        remediation_window = "1-2 weeks"
        business_impact = "Minor release delay, targeted remediation"

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Board Brief - Safety Release Block</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #1a1a2e;
            line-height: 1.6;
        }}
        .header {{
            border-bottom: 3px solid #dc3545;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #dc3545;
            margin: 0;
        }}
        .meta {{
            color: #6c757d;
            font-size: 14px;
            margin-top: 10px;
        }}
        .verdict {{
            background: #dc3545;
            color: white;
            padding: 15px 25px;
            border-radius: 8px;
            font-size: 24px;
            font-weight: bold;
            display: inline-block;
            margin: 20px 0;
        }}
        .section {{
            margin: 30px 0;
        }}
        .section h2 {{
            color: #16213e;
            border-bottom: 1px solid #e2e8f0;
            padding-bottom: 10px;
        }}
        .risk-item {{
            background: #f8f9fa;
            padding: 15px;
            border-left: 4px solid #dc3545;
            margin: 10px 0;
        }}
        .evidence {{
            background: #1a1a2e;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 4px;
            font-family: monospace;
            font-size: 12px;
            overflow-x: auto;
        }}
        .action-required {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 8px;
            margin: 20px 0;
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
        <h1>🛡️ Board Brief — Safety Release Block</h1>
        <div class="meta">
            <strong>Release Candidate:</strong> {release}<br/>
            <strong>Generated:</strong> {timestamp}<br/>
            <strong>Classification:</strong> Internal - Executive Review
        </div>
    </div>

    <div class="verdict">DECISION: {verdict}</div>

    <div class="section">
        <h2>Executive Summary</h2>
        <p>The automated safety gate has <strong>blocked</strong> the release of {release} due to identified safety regressions that exceed acceptable risk thresholds.</p>

        <div class="risk-item">
            <strong>Primary Risk:</strong> {primary_risk}<br/>
            <strong>Severity:</strong> {severity.upper()}<br/>
            <strong>Regressions Detected:</strong> {total_regressions}<br/>
            <strong>Critical Failures:</strong> {critical_failures}
        </div>
    </div>

    <div class="section">
        <h2>Business Impact</h2>
        <ul>
            <li><strong>Impact:</strong> {business_impact}</li>
            <li><strong>Estimated Remediation Window:</strong> {remediation_window}</li>
            <li><strong>Manual Override:</strong> Disabled (requires Safety Director approval)</li>
        </ul>
    </div>

    <div class="section">
        <h2>Evidence Summary</h2>
        <div class="evidence">
{json.dumps(summary, indent=2)}
        </div>
    </div>

    <div class="action-required">
        <strong>⚠️ Action Required</strong>
        <p>This block requires executive acknowledgment. Options:</p>
        <ol>
            <li>Wait for engineering remediation ({remediation_window})</li>
            <li>Request Safety Exception from authorized approver</li>
            <li>Escalate to Safety Board for risk acceptance review</li>
        </ol>
    </div>

    <div class="section">
        <h2>Decision Log</h2>
        <p>Release blocked by automated safety gate at {timestamp}.</p>
        <p>Gate policy: Zero tolerance for critical safety regressions.</p>
        <p>Override mechanism: Requires documented Safety Exception with TTL.</p>
    </div>

    <div class="footer">
        <p>Generated by Model Safety Regression Suite | Constitution-as-Code Governance</p>
        <p>This document is auto-generated for board-level visibility into AI safety decisions.</p>
    </div>
</body>
</html>"""

    return html


def main():
    parser = argparse.ArgumentParser(
        description="Generate Board Brief for Safety Release Block"
    )
    parser.add_argument(
        "--input", "-i",
        type=Path,
        default=GATE_PATH,
        help="Path to gate_report.json"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output HTML path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("BOARD BRIEF GENERATOR")
    print("=" * 60)

    gate = load_gate_report(args.input)
    html = generate_board_brief(gate)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html)

    print(f"\n[OK] Board brief generated: {args.output}")
    print(f"[OK] Release: {gate.get('release_candidate')}")
    print(f"[OK] Verdict: {gate.get('verdict')}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
