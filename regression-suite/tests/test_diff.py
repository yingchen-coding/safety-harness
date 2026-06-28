"""Tests for regression diffing (core/diff.py).

The direction-sensitive regression rule (higher-is-worse vs lower-is-worse) and the root-cause
attribution map are the load-bearing logic here; both are exercised without the run engine by
constructing MetricDiff lists directly.
"""
from core.diff import DiffEngine, MetricDiff


def _diff(metric, baseline, candidate, higher_is_worse):
    delta = None if baseline is None or candidate is None else candidate - baseline
    delta_pct = None if delta is None or baseline in (None, 0) else delta / baseline * 100
    return MetricDiff(
        suite="misuse", metric=metric, baseline_value=baseline, candidate_value=candidate,
        delta=delta, delta_pct=delta_pct, higher_is_worse=higher_is_worse,
    )


def test_is_regression_respects_metric_direction():
    # higher-is-worse: an increase is a regression, a decrease is not
    assert _diff("violation_rate", 0.05, 0.09, True).is_regression() is True
    assert _diff("violation_rate", 0.09, 0.05, True).is_regression() is False
    # lower-is-worse: a decrease is a regression, an increase is not
    assert _diff("avg_first_failure", 5.0, 3.0, False).is_regression() is True
    assert _diff("avg_first_failure", 3.0, 5.0, False).is_regression() is False
    # missing delta is never a regression
    assert _diff("violation_rate", None, 0.09, True).is_regression() is False


def test_engine_partitions_into_regression_improvement_neutral():
    eng = DiffEngine()
    diffs = [
        _diff("violation_rate", 0.05, 0.09, True),       # regression
        _diff("hedging_rate", 0.10, 0.04, True),         # improvement
        _diff("attack_success_rate", 0.20, 0.20, True),  # neutral (no change)
    ]
    summary = eng.summarize(diffs)
    assert summary["regressions"] == 1
    assert summary["improvements"] == 1
    assert summary["neutral"] == 1
    assert summary["total_metrics"] == 3
    assert summary["regressed_metrics"] == ["violation_rate"]
    assert summary["improved_metrics"] == ["hedging_rate"]


def test_get_regressions_and_improvements_are_disjoint():
    eng = DiffEngine()
    diffs = [
        _diff("violation_rate", 0.05, 0.09, True),
        _diff("avg_first_failure", 5.0, 3.0, False),
        _diff("hedging_rate", 0.10, 0.04, True),
    ]
    regs = {d.metric for d in eng.get_regressions(diffs)}
    imps = {d.metric for d in eng.get_improvements(diffs)}
    assert regs == {"violation_rate", "avg_first_failure"}
    assert imps == {"hedging_rate"}
    assert regs.isdisjoint(imps)


def test_attribute_root_causes_maps_regressions_to_failure_types_ranked():
    eng = DiffEngine()
    diffs = [
        _diff("policy_erosion_slope", 0.0, 0.12, True),   # -> trajectory_drift
        _diff("delayed_failure_rate", 0.0, 0.15, True),   # -> multi_turn_exploitation
        _diff("violation_rate", 0.0, 0.02, True),         # below 0.03 threshold -> ignored
    ]
    causes = eng.attribute_root_causes(diffs)
    assert "trajectory_drift" in causes
    assert "multi_turn_exploitation" in causes
    assert "policy_boundary_shift" not in causes  # under threshold
    # confidences are bounded in (0, 1] and returned in descending order
    vals = list(causes.values())
    assert all(0 < v <= 0.9 for v in vals)
    assert vals == sorted(vals, reverse=True)


def test_to_dict_includes_derived_regression_flag():
    d = _diff("violation_rate", 0.05, 0.09, True).to_dict()
    assert d["is_regression"] is True
    assert d["metric"] == "violation_rate"
    assert d["higher_is_worse"] is True
