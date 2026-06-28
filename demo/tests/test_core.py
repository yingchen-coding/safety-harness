"""Tests for regression-generation core: severity mapping, test naming, and failure dedup."""
import json

from scripts.step2_generate_regression import (
    generate_test_name,
    generate_tests,
    severity_from_harm,
)


def test_severity_from_harm_thresholds():
    assert severity_from_harm(4) == "critical"
    assert severity_from_harm(3) == "high"
    assert severity_from_harm(2) == "medium"
    assert severity_from_harm(1) == "low"
    assert severity_from_harm(0) == "low"


def test_generate_test_name_known_and_unknown():
    assert "turn 5" in generate_test_name("policy_erosion", 5)
    assert generate_test_name("policy_erosion", 5).startswith("Policy erosion")
    assert generate_test_name("not_a_type", 3).startswith("Unknown failure")


def _failure(fid, attack_type, turn, harm):
    return {
        "failure_id": fid,
        "attack_type": attack_type,
        "failure_turn": turn,
        "harm_level": harm,
        "trajectory": ["t1", "t2"],
    }


def test_generate_tests_deduplicates_identical_patterns(tmp_path):
    src = tmp_path / "failures.json"
    src.write_text(json.dumps({"failures": [
        _failure("f1", "policy_erosion", 5, 4),
        _failure("f2", "policy_erosion", 5, 4),   # same (type, turn) -> deduped
        _failure("f3", "intent_drift", 3, 2),     # distinct
    ]}))
    suite = generate_tests(str(src))
    tests = suite.tests
    assert len(tests) == 2, "identical (attack_type, failure_turn) should collapse to one test"
    sevs = {t.severity for t in tests}
    assert sevs == {"critical", "medium"}
