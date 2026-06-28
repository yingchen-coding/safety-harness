"""
Incident-to-Regression promotion pipeline.

Converts production incidents into permanent regression test artifacts
that become release gates for future deployments.

Closed-Loop Integration:
- Promotes incidents to regression tests
- Clears alignment debt when mitigations are verified
- Updates gate policy exception whitelist

Usage:
    python pipeline.py --incident incidents/INC_004.json
    python pipeline.py --all  # Promote all incidents
    python pipeline.py --clear-debt INC_004  # Mark debt as mitigated
"""

import argparse
import json
from pathlib import Path
from typing import List
from datetime import datetime

from taxonomy import map_incident_to_taxonomy, get_failure_weight
from debt_clearing import DebtClearer, clear_debt_for_incident


REGRESSION_DIR = Path("tests/regressions")


def promote_incident_to_regression(incident_path: Path) -> Path:
    """
    Convert a production incident into a regression test artifact.

    The regression case captures:
    - The trajectory pattern that led to failure
    - Expected blocking turn
    - Failure taxonomy classification
    - Severity weight for prioritization

    Args:
        incident_path: Path to incident JSON file

    Returns:
        Path to generated regression case
    """
    REGRESSION_DIR.mkdir(parents=True, exist_ok=True)

    with open(incident_path, "r", encoding="utf-8") as f:
        incident = json.load(f)

    incident_id = incident.get("incident_id", incident.get("id", "UNKNOWN"))
    failure_type = incident.get("failure_type", "unknown")

    # Extract trajectory (support both formats)
    trajectory = incident.get("trajectory", incident.get("conversation", []))

    # Find violation turns
    violation_turns = [
        t.get("turn", i + 1)
        for i, t in enumerate(trajectory)
        if t.get("violation", False) or t.get("status") == "unsafe"
    ]

    min_block_turn = min(violation_turns) if violation_turns else None

    # Map to taxonomy
    taxonomy_types = map_incident_to_taxonomy(failure_type)
    max_weight = max(
        (get_failure_weight(ft) for ft in taxonomy_types),
        default=1.0
    )

    # Build regression case
    regression_case = {
        "test_id": f"regression_{incident_id}",
        "source_incident": incident_id,
        "title": incident.get("title", "Unknown incident"),
        "failure_type": failure_type,
        "taxonomy_types": [ft.value for ft in taxonomy_types],
        "severity_weight": max_weight,
        "trajectory": _extract_test_trajectory(trajectory),
        "expected_behavior": {
            "should_block": True,
            "block_by_turn": min_block_turn,
            "expected_action": "HARD_STOP" if max_weight >= 1.5 else "SOFT_STOP"
        },
        "metadata": {
            "promoted_at": datetime.now().isoformat(),
            "source_file": str(incident_path),
            "root_causes": incident.get("root_causes", []),
            "mitigation_hints": incident.get("mitigation_hints", [])
        },
        "tags": ["regression", "postmortem", failure_type]
    }

    out_path = REGRESSION_DIR / f"{incident_id}.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(regression_case, f, indent=2)

    return out_path


def _extract_test_trajectory(trajectory: List[dict]) -> List[dict]:
    """Extract minimal trajectory for testing."""
    test_turns = []
    for turn in trajectory:
        test_turn = {
            "turn": turn.get("turn", len(test_turns) + 1),
            "role": turn.get("role", "unknown"),
            "content_preview": turn.get("content", "")[:100],
        }
        if turn.get("violation") or turn.get("status") == "unsafe":
            test_turn["expected_violation"] = True
        test_turns.append(test_turn)
    return test_turns


def promote_all_incidents(incidents_dir: Path = Path("incidents")) -> List[Path]:
    """Promote all incidents in directory to regression cases."""
    promoted = []
    for incident_file in incidents_dir.glob("INC_*.json"):
        try:
            out_path = promote_incident_to_regression(incident_file)
            promoted.append(out_path)
            print(f"[OK] {incident_file.name} -> {out_path}")
        except Exception as e:
            print(f"[FAIL] {incident_file.name}: {e}")
    return promoted


def promote_and_clear_debt(incident_path: Path) -> dict:
    """
    Promote incident to regression and clear associated alignment debt.

    This is the key closed-loop operation:
    1. Promote incident to permanent regression test
    2. Mark alignment debt as mitigated
    3. Return summary of actions taken

    Args:
        incident_path: Path to incident JSON file

    Returns:
        Summary of promotion and debt clearing
    """
    result = {
        "incident_path": str(incident_path),
        "regression_promoted": False,
        "debt_cleared": False,
        "regression_tests": [],
        "debt_entry": None
    }

    # Step 1: Promote to regression
    try:
        regression_path = promote_incident_to_regression(incident_path)
        result["regression_promoted"] = True
        result["regression_path"] = str(regression_path)

        # Load the regression case to get test ID
        with open(regression_path) as f:
            regression_case = json.load(f)
        test_id = regression_case.get("test_id", "unknown")
        result["regression_tests"].append(test_id)

    except Exception as e:
        result["promotion_error"] = str(e)
        return result

    # Step 2: Clear alignment debt
    try:
        incident_id = incident_path.stem  # e.g., "INC_004"
        debt_entry = clear_debt_for_incident(incident_id, result["regression_tests"])

        if debt_entry:
            result["debt_cleared"] = True
            result["debt_entry"] = {
                "debt_id": debt_entry.get("debt_id"),
                "principle": debt_entry.get("principle"),
                "mitigation_status": debt_entry.get("mitigation_status")
            }
        else:
            result["debt_note"] = f"No debt entry found for {incident_id}"

    except Exception as e:
        result["debt_clearing_error"] = str(e)

    return result


def clear_debt_only(incident_id: str, evidence: List[str] = None) -> dict:
    """
    Clear alignment debt for an incident without re-promoting.

    Use when regression test already exists but debt wasn't cleared.

    Args:
        incident_id: The incident ID (e.g., "INC_004")
        evidence: Optional list of regression test IDs

    Returns:
        Debt clearing result
    """
    evidence = evidence or [f"regression_{incident_id}"]
    clearer = DebtClearer()
    debt_entry = clearer.mark_mitigated(incident_id, evidence)

    return {
        "incident_id": incident_id,
        "debt_cleared": bool(debt_entry),
        "debt_entry": debt_entry if debt_entry else None
    }


def generate_debt_report() -> str:
    """Generate alignment debt status report."""
    clearer = DebtClearer()
    return clearer.generate_debt_report()


def verify_regression_coverage(regression_dir: Path = REGRESSION_DIR) -> dict:
    """Verify regression test coverage statistics."""
    if not regression_dir.exists():
        return {"error": "No regression directory found"}

    cases = list(regression_dir.glob("*.json"))
    if not cases:
        return {"error": "No regression cases found"}

    stats = {
        "total_cases": len(cases),
        "by_failure_type": {},
        "by_severity": {"critical": 0, "high": 0, "medium": 0, "low": 0},
        "coverage_gaps": []
    }

    for case_path in cases:
        if case_path.name == ".gitkeep":
            continue
        with open(case_path) as f:
            case = json.load(f)

        ft = case.get("failure_type", "unknown")
        stats["by_failure_type"][ft] = stats["by_failure_type"].get(ft, 0) + 1

        weight = case.get("severity_weight", 1.0)
        if weight >= 1.7:
            stats["by_severity"]["critical"] += 1
        elif weight >= 1.4:
            stats["by_severity"]["high"] += 1
        elif weight >= 1.1:
            stats["by_severity"]["medium"] += 1
        else:
            stats["by_severity"]["low"] += 1

    # Check for gaps
    expected_types = ["prompt_injection", "policy_erosion", "tool_hallucination",
                      "coordinated_misuse", "escalation_delay"]
    for ft in expected_types:
        if ft not in stats["by_failure_type"]:
            stats["coverage_gaps"].append(ft)

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Promote incidents to regression test cases and manage alignment debt"
    )
    parser.add_argument("--incident", type=str, help="Path to incident JSON")
    parser.add_argument("--all", action="store_true", help="Promote all incidents")
    parser.add_argument("--verify", action="store_true", help="Verify coverage")
    parser.add_argument("--clear-debt", type=str, metavar="INC_ID",
                        help="Clear alignment debt for incident (e.g., INC_004)")
    parser.add_argument("--debt-report", action="store_true",
                        help="Show alignment debt status report")
    parser.add_argument("--promote-and-clear", type=str, metavar="INCIDENT_PATH",
                        help="Promote incident AND clear associated debt")
    parser.add_argument("--evidence", type=str, nargs="+", default=[],
                        help="Evidence test IDs for debt clearing")
    args = parser.parse_args()

    if args.debt_report:
        print(generate_debt_report())
        return

    if args.clear_debt:
        result = clear_debt_only(args.clear_debt, args.evidence or None)
        if result["debt_cleared"]:
            print(f"[OK] Debt cleared for {args.clear_debt}")
            print(f"     Debt ID: {result['debt_entry'].get('debt_id')}")
            print("     Status: mitigated")
        else:
            print(f"[WARN] No matching debt found for {args.clear_debt}")
        return

    if args.promote_and_clear:
        result = promote_and_clear_debt(Path(args.promote_and_clear))
        print("\n=== Promote and Clear Result ===")
        print(f"Regression promoted: {result['regression_promoted']}")
        print(f"Debt cleared: {result['debt_cleared']}")
        if result.get("regression_path"):
            print(f"Regression path: {result['regression_path']}")
        if result.get("debt_entry"):
            print(f"Debt ID: {result['debt_entry'].get('debt_id')}")
        return

    if args.verify:
        stats = verify_regression_coverage()
        print("\n=== Regression Coverage ===")
        print(json.dumps(stats, indent=2))
        return

    if args.all:
        promoted = promote_all_incidents()
        print(f"\nPromoted {len(promoted)} incidents to regression cases")
        return

    if args.incident:
        out_path = promote_incident_to_regression(Path(args.incident))
        print(f"Promoted to regression: {out_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
