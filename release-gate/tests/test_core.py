"""Tests for the safety-budget calculation that gates releases."""
import pytest

from core.budget_metrics import SafetyBudget, calculate_safety_budget


def test_safety_budget_within_budget():
    b = calculate_safety_budget(failure_rate=0.05, total_budget=0.10)
    assert isinstance(b, SafetyBudget)
    assert b.current_failure_rate == 0.05
    assert b.total_budget == 0.10
    assert b.budget_remaining == pytest.approx(0.05)
    assert b.budget_consumed_pct == pytest.approx(0.5)
    assert b.status in {"GREEN", "YELLOW", "RED", "CRITICAL"}


def test_safety_budget_over_budget_has_no_remaining():
    b = calculate_safety_budget(failure_rate=0.15, total_budget=0.10)
    assert b.budget_remaining <= 0
    assert b.status in {"GREEN", "YELLOW", "RED", "CRITICAL"}
