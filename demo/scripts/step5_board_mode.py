#!/usr/bin/env python3
"""
Step 5: Safety Board Mode - Executive Governance Artifacts

Aggregates board-level safety artifacts from the regression suite
and generates unified executive dashboard.

This step demonstrates how safety systems can produce
board-level governance outputs automatically.

Usage:
    python scripts/step5_board_mode.py
    python scripts/step5_board_mode.py --generate-all
"""

import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

DEMO_ROOT = Path(__file__).resolve().parents[1]
REGRESSION_SUITE = DEMO_ROOT.parent / "model-safety-regression-suite"

BOARD_ARTIFACTS = [
    "board_brief_v1.html",
    "ceo_board_exception_audit.html",
    "quarterly_safety_investment_recommendation.md"
]

DST = DEMO_ROOT / "artifacts" / "board_mode"


def generate_board_artifacts():
    """Generate board artifacts in regression suite."""
    print("\n[Step 5a] Generating Board Artifacts...")

    scripts = [
        "scripts/generate_board_brief.py",
        "scripts/generate_exception_audit_report.py",
        "scripts/generate_safety_investment_recommendation.py"
    ]

    for script in scripts:
        script_path = REGRESSION_SUITE / script
        if script_path.exists():
            print(f"  Running: {script}")
            result = subprocess.run(
                ["python", str(script_path)],
                cwd=REGRESSION_SUITE,
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"    Warning: {script} returned non-zero")
                if result.stderr:
                    print(f"    {result.stderr[:200]}")
        else:
            print(f"  Skipping (not found): {script}")


def copy_board_artifacts():
    """Copy board artifacts to demo."""
    print("\n[Step 5b] Copying Board Artifacts to Demo...")

    DST.mkdir(parents=True, exist_ok=True)

    src_dir = REGRESSION_SUITE / "artifacts"
    copied = 0

    for artifact in BOARD_ARTIFACTS:
        src = src_dir / artifact
        if src.exists():
            shutil.copy(src, DST / artifact)
            print(f"  Copied: {artifact}")
            copied += 1
        else:
            print(f"  Not found: {artifact}")

    return copied


def generate_board_index():
    """Generate index page for board artifacts."""
    print("\n[Step 5c] Generating Board Mode Index...")

    timestamp = datetime.now().astimezone().isoformat()

    # Check which artifacts exist
    artifacts_status = []
    for artifact in BOARD_ARTIFACTS:
        path = DST / artifact
        exists = path.exists()
        artifacts_status.append({
            "name": artifact,
            "exists": exists,
            "path": f"board_mode/{artifact}" if exists else None
        })

    html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Safety Board Mode - Executive Dashboard</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e2e8f0;
            margin: 0;
            min-height: 100vh;
            padding: 40px;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
        }}
        .header {{
            text-align: center;
            padding: 40px 0;
            border-bottom: 2px solid rgba(255,255,255,0.1);
        }}
        .header h1 {{
            font-size: 48px;
            margin: 0;
            background: linear-gradient(90deg, #ffc107, #fd7e14);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        .header p {{
            color: #94a3b8;
            margin-top: 10px;
        }}
        .cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 40px;
        }}
        .card {{
            background: rgba(255,255,255,0.05);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 12px;
            padding: 25px;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 40px rgba(0,0,0,0.3);
        }}
        .card h3 {{
            margin: 0 0 15px 0;
            color: #ffc107;
        }}
        .card p {{
            color: #94a3b8;
            font-size: 14px;
            line-height: 1.6;
        }}
        .card a {{
            display: inline-block;
            margin-top: 15px;
            padding: 10px 20px;
            background: #ffc107;
            color: #1a1a2e;
            text-decoration: none;
            border-radius: 6px;
            font-weight: bold;
            transition: background 0.2s;
        }}
        .card a:hover {{
            background: #fd7e14;
        }}
        .card .unavailable {{
            color: #6c757d;
            font-style: italic;
        }}
        .governance-level {{
            text-align: center;
            margin: 40px 0;
            padding: 30px;
            background: rgba(255,193,7,0.1);
            border: 1px solid #ffc107;
            border-radius: 12px;
        }}
        .governance-level h2 {{
            color: #ffc107;
            margin: 0;
        }}
        .footer {{
            text-align: center;
            margin-top: 60px;
            padding-top: 20px;
            border-top: 1px solid rgba(255,255,255,0.1);
            color: #6c757d;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏛️ Safety Board Mode</h1>
            <p>Executive-Level AI Safety Governance Dashboard</p>
            <p style="font-size: 12px;">Generated: {timestamp}</p>
        </div>

        <div class="governance-level">
            <h2>Board-Level Safety Governance Active</h2>
            <p>This system automatically escalates safety decisions to executive visibility</p>
        </div>

        <div class="cards">
            <div class="card">
                <h3>📋 Board Brief</h3>
                <p>One-page executive summary generated when releases are BLOCKED. Includes risk assessment, business impact, and remediation timeline.</p>
                {"<a href='board_mode/board_brief_v1.html'>View Brief</a>" if (DST / "board_brief_v1.html").exists() else "<p class='unavailable'>Not yet generated</p>"}
            </div>

            <div class="card">
                <h3>🔒 Exception Audit</h3>
                <p>CEO/Board audit report for safety exceptions. Tracks governance risk, exception patterns, and renewal history.</p>
                {"<a href='board_mode/ceo_board_exception_audit.html'>View Audit</a>" if (DST / "ceo_board_exception_audit.html").exists() else "<p class='unavailable'>Not yet generated</p>"}
            </div>

            <div class="card">
                <h3>💰 Investment Recommendation</h3>
                <p>Quarterly safety investment recommendations based on alignment debt patterns. Includes FTE estimates and ROI framing.</p>
                {"<a href='board_mode/quarterly_safety_investment_recommendation.md'>View Recommendation</a>" if (DST / "quarterly_safety_investment_recommendation.md").exists() else "<p class='unavailable'>Not yet generated</p>"}
            </div>
        </div>

        <div class="footer">
            <p>Generated by Agentic Safety Demo | Constitution-as-Code Governance System</p>
            <p>Safety Board Mode elevates AI safety from engineering to board-level governance</p>
        </div>
    </div>
</body>
</html>"""

    index_path = DEMO_ROOT / "artifacts" / "board_mode_index.html"
    index_path.write_text(html)
    print(f"  Generated: {index_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Step 5: Safety Board Mode - Executive Governance"
    )
    parser.add_argument(
        "--generate-all",
        action="store_true",
        help="Generate all board artifacts before copying"
    )
    parser.add_argument(
        "--copy-only",
        action="store_true",
        help="Only copy existing artifacts without generating"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("STEP 5: SAFETY BOARD MODE")
    print("=" * 60)
    print("\nElevating safety governance to board level...")

    if not args.copy_only:
        generate_board_artifacts()

    copied = copy_board_artifacts()
    generate_board_index()

    print("\n" + "=" * 60)
    print(f"[OK] Board Mode artifacts: {copied}/{len(BOARD_ARTIFACTS)}")
    print("[OK] Index: artifacts/board_mode_index.html")
    print("=" * 60)


if __name__ == "__main__":
    main()
