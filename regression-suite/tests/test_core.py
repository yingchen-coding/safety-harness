"""Tests for adapter validation and the misuse adapter's result invariants."""
import random

from adapters.base import validate_adapter
from adapters.misuse import MisuseAdapter, MisuseResult


def test_validate_adapter_rejects_non_adapter():
    assert validate_adapter(object()) is False
    assert validate_adapter("not an adapter") is False


def test_misuse_run_counts_are_self_consistent():
    random.seed(0)
    result = MisuseAdapter(scenario_count=20).run("test-model")
    assert isinstance(result, MisuseResult)
    assert result.model == "test-model"
    assert result.total_scenarios == 20
    # every scenario is exactly one of violation / hedging / compliant
    assert result.violations + result.hedging + result.compliant == 20
    # rates are derived consistently from the counts and stay in [0, 1]
    assert result.violation_rate == result.violations / 20
    assert result.hedging_rate == result.hedging / 20
    assert 0.0 <= result.violation_rate <= 1.0
    assert 0.0 <= result.hedging_rate <= 1.0


def test_misuse_result_to_dict_roundtrips_model():
    random.seed(1)
    d = MisuseAdapter(scenario_count=5).run("m").to_dict()
    assert isinstance(d, dict)
    assert d.get("model") == "m"
