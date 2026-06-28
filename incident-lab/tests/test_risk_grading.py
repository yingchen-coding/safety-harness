"""Boundary tests for regression-aware risk grading (risk_grading.py).

The grader turns blast-radius metrics into OK/WARN/BLOCK release verdicts. These tests pin the
threshold boundaries and the CI exit-code contract, which is what downstream CI/CD relies on.
"""
from risk_grading import (
    THRESHOLDS,
    BlastRadius,
    RiskVerdict,
    compute_blast_radius,
    format_blast_radius_report,
    get_exit_code,
    grade_risk,
)


def _br(**kw):
    base = dict(
        affected_categories={},
        delayed_failure_rate=0.0,
        policy_erosion_delta=0.0,
        regression_flag=False,
    )
    base.update(kw)
    return BlastRadius(**base)


def test_compute_blast_radius_reads_metric_dict_with_defaults():
    br = compute_blast_radius({
        "category_deltas": {"prompt_injection": 0.12, "intent_drift": 0.24},
        "delayed_failure_delta": 0.18,
        "policy_erosion_delta": 0.22,
        "regression_flag": True,
        "incident_count": 3,
    })
    assert br.max_category_delta() == 0.24
    assert br.affected_category_count() == 2
    assert br.regression_flag is True
    assert br.incident_count == 3
    # missing keys fall back to inert defaults
    empty = compute_blast_radius({})
    assert empty.max_category_delta() == 0.0
    assert empty.regression_flag is False
    assert empty.incident_count == 1


def test_clean_metrics_grade_ok():
    assert grade_risk(_br()) is RiskVerdict.OK


def test_block_requires_regression_flag_even_with_high_deltas():
    # high erosion but no regression flag -> not a BLOCK; it still trips a WARN
    no_flag = _br(policy_erosion_delta=0.99, regression_flag=False)
    assert grade_risk(no_flag) is RiskVerdict.WARN
    # same delta WITH the flag -> BLOCK
    flagged = _br(policy_erosion_delta=0.99, regression_flag=True)
    assert grade_risk(flagged) is RiskVerdict.BLOCK


def test_each_block_threshold_independently_blocks():
    assert grade_risk(_br(regression_flag=True,
                          policy_erosion_delta=THRESHOLDS['policy_erosion_block'] + 0.01)) is RiskVerdict.BLOCK
    assert grade_risk(_br(regression_flag=True,
                          delayed_failure_rate=THRESHOLDS['delayed_failure_block'] + 0.01)) is RiskVerdict.BLOCK
    assert grade_risk(_br(regression_flag=True,
                          affected_categories={"c": THRESHOLDS['category_delta_block'] + 0.01})) is RiskVerdict.BLOCK


def test_warn_band_between_warn_and_block_thresholds():
    mid = (THRESHOLDS['policy_erosion_warn'] + THRESHOLDS['policy_erosion_block']) / 2
    assert grade_risk(_br(policy_erosion_delta=mid)) is RiskVerdict.WARN


def test_three_affected_categories_warn_even_when_each_is_small():
    small = THRESHOLDS['category_delta_warn'] - 0.02  # below warn delta individually
    br = _br(affected_categories={"a": 0.06, "b": 0.06, "c": 0.06})
    assert br.affected_category_count() == 3
    assert br.max_category_delta() < THRESHOLDS['category_delta_warn']
    assert grade_risk(br) is RiskVerdict.WARN
    assert small  # silence lint on the explanatory binding


def test_exit_codes_match_ci_contract():
    assert get_exit_code(RiskVerdict.OK) == 0
    assert get_exit_code(RiskVerdict.BLOCK) == 1
    assert get_exit_code(RiskVerdict.WARN) == 2


def test_report_renders_verdict_and_categories():
    br = _br(affected_categories={"prompt_injection": 0.3}, policy_erosion_delta=0.2, regression_flag=True)
    verdict = grade_risk(br)
    report = format_blast_radius_report(br, verdict)
    assert "BLAST RADIUS REPORT" in report
    assert verdict.value in report
    assert "prompt_injection" in report
