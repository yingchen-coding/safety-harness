"""
HTML report generator for regression results.
"""

from datetime import datetime
from typing import Optional

from core import RunResult, MetricDiff, RiskReport, Verdict


class HTMLReporter:
    """
    Generates HTML regression reports.
    """

    def generate(
        self,
        run_result: RunResult,
        diffs: list[MetricDiff],
        risk_report: RiskReport,
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate HTML report.

        Args:
            run_result: Evaluation results
            diffs: Metric diffs
            risk_report: Risk assessment
            output_path: Optional path to save HTML

        Returns:
            HTML string
        """
        verdict_colors = {
            Verdict.OK: ('#10b981', '✅'),
            Verdict.WARN: ('#f59e0b', '⚠️'),
            Verdict.BLOCK: ('#ef4444', '❌')
        }

        color, icon = verdict_colors[risk_report.verdict]

        # Generate metric rows
        metric_rows = []
        for diff in sorted(diffs, key=lambda d: (d.suite, d.metric)):
            if diff.delta is None:
                continue

            # Determine status
            regression = next(
                (r for r in risk_report.regressions if r.metric_diff.metric == diff.metric),
                None
            )

            if regression:
                if regression.severity == 'block':
                    status = '<span style="color: #ef4444;">🔴 BLOCK</span>'
                else:
                    status = '<span style="color: #f59e0b;">🟡 WARN</span>'
            elif diff.is_regression():
                status = '<span style="color: #6b7280;">⚪ Minor</span>'
            elif diff.delta < 0 and diff.higher_is_worse:
                status = '<span style="color: #10b981;">🟢 Improved</span>'
            else:
                status = '<span style="color: #6b7280;">⚪ Stable</span>'

            baseline_str = f"{diff.baseline_value:.3f}" if diff.baseline_value else "N/A"
            candidate_str = f"{diff.candidate_value:.3f}" if diff.candidate_value else "N/A"
            delta_str = f"{diff.delta:+.3f}" if diff.delta else "N/A"

            metric_rows.append(f"""
                <tr>
                    <td>{diff.suite}</td>
                    <td>{diff.metric}</td>
                    <td>{baseline_str}</td>
                    <td>{candidate_str}</td>
                    <td>{delta_str}</td>
                    <td>{status}</td>
                </tr>
            """)

        # Generate regression list
        regression_items = []
        for r in risk_report.regressions:
            icon_r = "🔴" if r.severity == 'block' else "🟡"
            regression_items.append(f"<li>{icon_r} <strong>[{r.metric_diff.suite}]</strong> {r.message}</li>")

        regression_html = "<ul>" + "\n".join(regression_items) + "</ul>" if regression_items else "<p>None</p>"

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Safety Regression Report</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f9fafb;
        }}
        h1 {{ color: #111827; }}
        h2 {{ color: #374151; border-bottom: 2px solid #e5e7eb; padding-bottom: 8px; }}
        .verdict-box {{
            background: {color}15;
            border: 2px solid {color};
            border-radius: 8px;
            padding: 24px;
            text-align: center;
            margin: 20px 0;
        }}
        .verdict-text {{
            font-size: 32px;
            font-weight: bold;
            color: {color};
        }}
        .summary {{
            font-size: 16px;
            color: #4b5563;
            margin-top: 12px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        th {{
            background: #f3f4f6;
            padding: 12px;
            text-align: left;
            font-weight: 600;
            color: #374151;
        }}
        td {{
            padding: 12px;
            border-top: 1px solid #e5e7eb;
        }}
        tr:hover {{ background: #f9fafb; }}
        .meta {{
            background: white;
            padding: 16px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }}
        .meta-item {{
            display: inline-block;
            margin-right: 24px;
        }}
        .meta-label {{ color: #6b7280; font-size: 12px; }}
        .meta-value {{ color: #111827; font-weight: 500; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <h1>🛡️ Safety Regression Report</h1>

    <div class="meta">
        <div class="meta-item">
            <div class="meta-label">Baseline</div>
            <div class="meta-value">{run_result.baseline_model}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Candidate</div>
            <div class="meta-value">{run_result.candidate_model}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Suites</div>
            <div class="meta-value">{', '.join(run_result.suites)}</div>
        </div>
        <div class="meta-item">
            <div class="meta-label">Generated</div>
            <div class="meta-value">{datetime.now().strftime('%Y-%m-%d %H:%M')}</div>
        </div>
    </div>

    <div class="verdict-box">
        <div class="verdict-text">{icon} {risk_report.verdict.value.upper()}</div>
        <div class="summary">{risk_report.summary}</div>
    </div>

    <h2>📊 Metric Comparison</h2>
    <table>
        <thead>
            <tr>
                <th>Suite</th>
                <th>Metric</th>
                <th>Baseline</th>
                <th>Candidate</th>
                <th>Delta</th>
                <th>Status</th>
            </tr>
        </thead>
        <tbody>
            {''.join(metric_rows)}
        </tbody>
    </table>

    <h2>⚠️ Detected Regressions</h2>
    {regression_html}

    <h2>📋 Release Recommendation</h2>
    <p><strong>{risk_report.summary}</strong></p>

    <hr style="margin-top: 40px; border: none; border-top: 1px solid #e5e7eb;">
    <p style="color: #9ca3af; font-size: 12px;">
        Generated by <strong>model-safety-regression-suite</strong> · Release gating prototype for multi-turn safety evaluation
    </p>
</body>
</html>
        """

        if output_path:
            with open(output_path, 'w') as f:
                f.write(html)

        return html
