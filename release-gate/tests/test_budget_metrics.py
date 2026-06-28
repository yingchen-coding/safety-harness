"""Tests for safety-budget status bands, burn-rate projection, and weighted regression severity.

The existing test_core.py covers the happy/over-budget path; this pins the status thresholds,
the historical-trend projection, and the severity-level mapping that drive the gate recommendation.
"""
import pytest

from core.budget_metrics import (
    calculate_regression_severity,
    calculate_safety_budget,
    format_executive_summary,
)


def test_status_bands_track_budget_consumption():
    # Interior-band points (exact band boundaries are float-fragile, e.g. 0.08/0.10 != 0.8).
    assert calculate_safety_budget(0.0, 0.10).status == "GREEN"     # 0% consumed
    assert calculate_safety_budget(0.065, 0.10).status == "YELLOW"  # 65% consumed
    assert calculate_safety_budget(0.085, 0.10).status == "RED"     # 85% consumed
    assert calculate_safety_budget(0.10, 0.10).status == "CRITICAL"  # 100% consumed
    assert calculate_safety_budget(0.20, 0.10).status == "CRITICAL"  # over budget


def test_budget_remaining_never_negative_and_consumed_pct_tracks():
    b = calculate_safety_budget(0.25, 0.10)
    assert b.budget_remaining == 0  # clamped, not negative
    assert b.budget_consumed_pct == pytest.approx(2.5)


def test_rising_history_projects_a_finite_breach_horizon():
    b = calculate_safety_budget(
        failure_rate=0.07, total_budget=0.10,
        historical_rates=[0.04, 0.05, 0.06, 0.07], releases_per_week=2.0,
    )
    assert b.burn_rate_per_release > 0
    assert b.projected_breach_releases is not None
    assert b.projected_breach_releases >= 0
    # weeks projection is consistent with releases / releases_per_week
    assert b.projected_breach_weeks == int(b.projected_breach_releases / 2.0)


def test_flat_or_declining_history_has_no_burn_and_no_projection():
    b = calculate_safety_budget(0.05, 0.10, historical_rates=[0.09, 0.07, 0.05])
    assert b.burn_rate_per_release == 0.0  # declining trend is floored at 0
    assert b.projected_breach_releases is None


def test_too_little_history_means_no_burn_rate():
    b = calculate_safety_budget(0.05, 0.10, historical_rates=[0.05])
    assert b.burn_rate_per_release == 0.0
    assert b.projected_breach_releases is None


def test_regression_severity_levels_and_actions():
    low = calculate_regression_severity(0.0, 0.0, 0.0, {})
    assert low.severity_level == "LOW" and low.recommended_action == "OK"
    assert low.severity_score == pytest.approx(0.0)

    severe = calculate_regression_severity(
        failure_rate_delta=0.20, erosion_slope_delta=0.20,
        avg_first_failure_delta=-4.0, high_risk_deltas={"tool_hallucination": 0.30},
    )
    # everything maxed out -> score saturates near 1.0 -> CRITICAL/BLOCK
    assert severe.severity_score == pytest.approx(1.0)
    assert severe.severity_level == "CRITICAL"
    assert severe.recommended_action == "BLOCK"


def test_regression_severity_top_contributors_are_ranked_and_nonzero():
    sev = calculate_regression_severity(
        failure_rate_delta=0.10, erosion_slope_delta=0.0,
        avg_first_failure_delta=0.0, high_risk_deltas={"a": 0.15, "b": 0.05},
    )
    # failure_rate dominates; only nonzero contributors are listed
    assert sev.top_contributors[0] == "failure_rate"
    assert "erosion_slope" not in sev.top_contributors  # zero contribution dropped
    assert "a" in sev.top_contributors  # the larger high-risk category wins


def test_executive_summary_reflects_gate_decision():
    budget = calculate_safety_budget(0.07, 0.10, historical_rates=[0.04, 0.055, 0.07])
    blocked = format_executive_summary(budget, "BLOCK")
    assert "BLOCK release" in blocked
    cleared = format_executive_summary(budget, "OK")
    assert "CLEAR TO RELEASE" in cleared
