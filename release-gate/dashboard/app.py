"""
Streamlit dashboard for evaluation monitoring.

Run with: streamlit run dashboard/app.py
"""

try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False
    print("Streamlit not installed. Run: pip install streamlit")

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from storage import MetricsStore
from monitoring import AlertDispatcher


def main():
    if not HAS_STREAMLIT:
        print("Dashboard requires streamlit. Install with: pip install streamlit")
        return

    st.set_page_config(
        page_title="Safeguards Eval Dashboard",
        page_icon="🛡️",
        layout="wide"
    )

    st.title("🛡️ Safeguards Evaluation Dashboard")

    # Sidebar
    st.sidebar.header("Navigation")
    page = st.sidebar.radio(
        "Select View",
        ["Overview", "Run Details", "Alerts", "Comparison"]
    )

    store = MetricsStore()
    alerter = AlertDispatcher()

    if page == "Overview":
        render_overview(store)
    elif page == "Run Details":
        render_run_details(store)
    elif page == "Alerts":
        render_alerts(alerter)
    elif page == "Comparison":
        render_comparison(store)


def render_overview(store: MetricsStore):
    """Render overview page."""
    st.header("📊 Evaluation Overview")

    runs = store.list_runs()

    if not runs:
        st.info("No evaluation runs found. Run `python run_batch.py` to create one.")
        return

    st.subheader(f"Available Runs ({len(runs)})")

    # Summary table
    summaries = []
    for run_id in runs[-10:]:  # Last 10 runs
        try:
            summary = store.compute_summary(run_id)
            summary['run_id'] = run_id
            summaries.append(summary)
        except Exception as e:
            st.warning(f"Could not load {run_id}: {e}")

    if summaries:
        st.dataframe(summaries)

        # Metrics over time
        st.subheader("Violation Rate Trend")
        violation_rates = [s['violation_rate'] for s in summaries]
        st.line_chart(violation_rates)


def render_run_details(store: MetricsStore):
    """Render detailed run view."""
    st.header("🔍 Run Details")

    runs = store.list_runs()
    if not runs:
        st.info("No runs available.")
        return

    selected_run = st.selectbox("Select Run", runs)

    if selected_run:
        try:
            metadata, results = store.load_run(selected_run)

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Metadata")
                st.json({
                    'run_id': metadata.run_id,
                    'tag': metadata.tag,
                    'models': metadata.models,
                    'timestamp': metadata.timestamp
                })

            with col2:
                st.subheader("Summary")
                summary = store.compute_summary(selected_run)
                st.metric("Total Scenarios", summary['total_scenarios'])
                st.metric("Violation Rate", f"{summary['violation_rate']:.1%}")
                st.metric("Avg First Failure", summary['avg_first_failure_turn'] or "N/A")

            # Results table
            st.subheader("Results")
            st.dataframe(results)

        except Exception as e:
            st.error(f"Error loading run: {e}")


def render_alerts(alerter: AlertDispatcher):
    """Render alerts page."""
    st.header("🚨 Alerts")

    alerts = alerter.get_recent_alerts(limit=50)

    if not alerts:
        st.success("No recent alerts.")
        return

    # Summary
    summary = alerter.get_alert_summary()
    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Total Alerts", summary['total_alerts'])
    with col2:
        critical = summary['by_severity'].get('critical', 0)
        st.metric("Critical", critical)
    with col3:
        warning = summary['by_severity'].get('warning', 0)
        st.metric("Warning", warning)

    # Alert list
    st.subheader("Recent Alerts")
    for alert in reversed(alerts[-20:]):
        severity = alert['severity']
        icon = "🔴" if severity == "critical" else "🟡" if severity == "warning" else "🔵"
        st.markdown(f"{icon} **{alert['message']}** ({alert['timestamp']})")


def render_comparison(store: MetricsStore):
    """Render run comparison page."""
    st.header("⚖️ Run Comparison")

    runs = store.list_runs()
    if len(runs) < 2:
        st.info("Need at least 2 runs to compare.")
        return

    col1, col2 = st.columns(2)

    with col1:
        baseline = st.selectbox("Baseline Run", runs, key="baseline")
    with col2:
        candidate = st.selectbox("Candidate Run", runs, index=min(1, len(runs)-1), key="candidate")

    if baseline and candidate and baseline != candidate:
        base_summary = store.compute_summary(baseline)
        cand_summary = store.compute_summary(candidate)

        st.subheader("Comparison")

        metrics = ['violation_rate', 'avg_first_failure_turn', 'avg_latency_ms']

        for metric in metrics:
            base_val = base_summary.get(metric, 0) or 0
            cand_val = cand_summary.get(metric, 0) or 0

            if isinstance(base_val, float) and metric == 'violation_rate':
                delta = f"{(cand_val - base_val):.1%}"
                base_display = f"{base_val:.1%}"
                cand_display = f"{cand_val:.1%}"
            else:
                delta = f"{cand_val - base_val:.2f}"
                base_display = f"{base_val:.2f}"
                cand_display = f"{cand_val:.2f}"

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{metric} (baseline)", base_display)
            with col2:
                st.metric(f"{metric} (candidate)", cand_display)
            with col3:
                st.metric("Delta", delta)


if __name__ == "__main__":
    main()
