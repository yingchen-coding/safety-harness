"""Tests for the declarative safeguard policy engine (safeguards/policy_dsl.py).

Covers priority resolution (the highest-priority matching rule wins), the supported condition
forms (numeric comparison, string equality, compound and/or), and the fail-safe default.
"""
from safeguards.api import Decision, GuardContext
from safeguards.policy_dsl import DEFAULT_POLICY, PolicyEngine


def _ctx(step=1, drift=0.0, violations=0):
    return GuardContext(
        run_id="t", step=step, conversation_history=[],
        cumulative_drift=drift, violation_count=violations,
    )


def _engine(rules=DEFAULT_POLICY):
    eng = PolicyEngine()
    eng.load_from_dict(rules)
    return eng


def test_rules_are_sorted_by_priority_descending():
    eng = _engine()
    priorities = [r.priority for r in eng.rules]
    assert priorities == sorted(priorities, reverse=True)


def test_numeric_threshold_rules_fire_by_band():
    eng = _engine()
    # high drift -> HARD_STOP
    assert eng.evaluate(_ctx(drift=0.6), {}).decision is Decision.HARD_STOP
    # moderate drift -> SOFT_STOP
    assert eng.evaluate(_ctx(drift=0.4), {}).decision is Decision.SOFT_STOP
    # low drift, nothing else -> PROCEED
    proceed = eng.evaluate(_ctx(drift=0.1), {})
    assert proceed.decision is Decision.PROCEED
    assert "No policy rule" in proceed.reason


def test_highest_priority_rule_wins_over_lower_priority_match():
    eng = _engine()
    # drift 0.6 alone would HARD_STOP via high_drift_block (prio 10);
    # a violation (prio 15) also matches and must be the one reported.
    decision = eng.evaluate(_ctx(drift=0.6, violations=1), {})
    assert decision.decision is Decision.HARD_STOP
    assert decision.features["matched_rule"] == "violation_block"


def test_string_equality_condition_uses_features():
    eng = _engine()
    decision = eng.evaluate(_ctx(drift=0.1), {"tool_risk": "high"})
    assert decision.decision is Decision.SOFT_STOP
    assert decision.features["matched_rule"] == "high_risk_tool"
    # a non-matching value falls through to PROCEED
    assert eng.evaluate(_ctx(drift=0.1), {"tool_risk": "low"}).decision is Decision.PROCEED


def test_compound_and_condition():
    eng = _engine([{
        "name": "risky_and_uncertain",
        "when": "tool_risk == 'high' and uncertainty < 0.6",
        "action": "SOFT_STOP",
        "reason": "high-risk tool with low confidence",
        "priority": 5,
    }])
    assert eng.evaluate(_ctx(), {"tool_risk": "high", "uncertainty": 0.4}).decision is Decision.SOFT_STOP
    # second clause false -> no match -> PROCEED
    assert eng.evaluate(_ctx(), {"tool_risk": "high", "uncertainty": 0.9}).decision is Decision.PROCEED


def test_identifier_containing_or_or_and_is_not_corrupted():
    # Regression guard: a naive substring replace of "or"/"and" used to corrupt the feature
    # name "drift_score" (contains "or"), so the default drift rules silently never fired.
    eng = _engine([{
        "name": "drift_block",
        "when": "drift_score > 0.5",
        "action": "HARD_STOP",
        "reason": "drift",
        "priority": 10,
    }])
    assert eng.evaluate(_ctx(drift=0.6), {}).decision is Decision.HARD_STOP
    # a custom feature whose name contains "and" must also evaluate, not silently fail
    eng2 = _engine([{
        "name": "bandwidth_rule",
        "when": "bandwidth_used > 0.9",
        "action": "SOFT_STOP",
        "reason": "bandwidth",
        "priority": 1,
    }])
    assert eng2.evaluate(_ctx(), {"bandwidth_used": 0.95}).decision is Decision.SOFT_STOP


def test_or_condition_matches_when_either_clause_holds():
    eng = _engine([{
        "name": "either",
        "when": "drift_score > 0.8 or violation_count > 0",
        "action": "HARD_STOP",
        "reason": "either trigger",
        "priority": 10,
    }])
    assert eng.evaluate(_ctx(drift=0.1, violations=1), {}).decision is Decision.HARD_STOP  # 2nd clause
    assert eng.evaluate(_ctx(drift=0.9, violations=0), {}).decision is Decision.HARD_STOP  # 1st clause
    assert eng.evaluate(_ctx(drift=0.1, violations=0), {}).decision is Decision.PROCEED    # neither


def test_malformed_condition_fails_safe_to_proceed():
    eng = _engine([{
        "name": "broken",
        "when": "this is not <<a valid>> condition !!!",
        "action": "HARD_STOP",
        "reason": "should never fire",
        "priority": 99,
    }])
    # a condition that cannot be parsed must NOT match (fail-safe), so we PROCEED
    assert eng.evaluate(_ctx(drift=0.9), {}).decision is Decision.PROCEED
