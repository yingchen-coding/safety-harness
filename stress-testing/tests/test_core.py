"""Core behavior tests: attack mutators, the template catalog, power analysis, and the red-team run."""
from analysis.power_analysis import compute_ci_width, compute_power, estimate_coverage
from attacks import mutators
from attacks.templates import (
    AttackTemplate,
    get_all_attacks,
    get_attack_by_id,
    get_attacks_by_category,
)
from demos.run_redteam import RedTeamReport, run_redteam


def test_mutators_return_nonempty_strings():
    p = "do the thing"
    for fn in (mutators.paraphrase, mutators.roleplay, mutators.escalate,
               mutators.decompose, mutators.obfuscate, mutators.hypothetical):
        out = fn(p)
        assert isinstance(out, str) and out.strip()


def test_decompose_carries_the_prompt_and_roleplay_uses_unknown_role():
    assert "do X" in mutators.decompose("do X", step=1)
    assert "pentester" in mutators.roleplay("do X", role="pentester")


def test_attack_catalog_is_well_formed():
    attacks = get_all_attacks()
    assert len(attacks) >= 4
    assert all(isinstance(a, AttackTemplate) and a.turns for a in attacks)
    ids = [a.id for a in attacks]
    assert len(ids) == len(set(ids)), "attack ids must be unique"


def test_get_attack_by_id_roundtrips_and_category_filters():
    first = get_all_attacks()[0]
    assert get_attack_by_id(first.id) is first
    assert get_attack_by_id("does-not-exist") is None
    jb = get_attacks_by_category("jailbreak")
    assert jb and all(a.category == "jailbreak" for a in jb)


def test_power_analysis_has_correct_monotonicity_and_bounds():
    # more samples -> narrower confidence interval
    assert compute_ci_width(1000) < compute_ci_width(50)
    # more samples -> at least as much power, capped below 1.0
    assert compute_power(1000) >= compute_power(20)
    assert compute_power(10_000) <= 0.99
    cov = estimate_coverage(500)
    assert 0.0 <= cov <= 1.0


def test_run_redteam_report_is_consistent():
    for mode in ("static", "adaptive"):
        report = run_redteam(mode, rollouts=25, safeguard_strength=0.5)
        assert isinstance(report, RedTeamReport)
        assert report.total_rollouts == 25
        assert len(report.results) == 25
        assert 0 <= report.violations <= 25
        assert isinstance(report.summary(), str)
