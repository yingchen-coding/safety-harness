#!/usr/bin/env python3
"""
Generate Safety ROI Model - Investment vs Risk Reduction

Translates alignment debt and safety investments into
board-level financial risk language.

Key outputs:
- Expected incident probability per debt
- Safety investment → risk reduction curve
- Dollar-denominated ROI framing

Usage:
    python scripts/generate_safety_roi_model.py
    python scripts/generate_safety_roi_model.py --output artifacts/safety_roi_model.json
"""

import yaml
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
EXCEPTIONS_PATH = ROOT / "artifacts" / "safety_exceptions.yaml"
OUTPUT_PATH = ROOT / "artifacts" / "safety_roi_model.json"

# Risk model parameters (calibrated heuristics)
BASE_INCIDENT_PROBABILITY = 0.02  # 2% base quarterly incident rate
DEBT_PROBABILITY_INCREMENT = 0.015  # +1.5% per open debt
CRITICAL_DEBT_MULTIPLIER = 3.0  # Critical debt has 3x impact
HIGH_DEBT_MULTIPLIER = 1.5  # High debt has 1.5x impact
EXCEPTION_RISK_INCREMENT = 0.005  # +0.5% per active exception

# Cost model parameters
AVERAGE_INCIDENT_COST = 500000  # $500k average incident cost
CRITICAL_INCIDENT_COST = 2000000  # $2M critical incident
SAFETY_FTE_COST = 250000  # $250k/year per safety FTE


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def calculate_incident_probability(debts: List[Dict], exceptions: List[Dict]) -> Dict:
    """Calculate expected incident probability based on debt and exceptions."""
    open_debts = [d for d in debts if d.get("status") == "open" or d.get("mitigation_status") == "open"]
    active_exceptions = [e for e in exceptions if e.get("status") == "active"]

    # Base probability
    probability = BASE_INCIDENT_PROBABILITY

    # Add debt risk
    for debt in open_debts:
        severity = debt.get("severity", "medium")
        if severity == "critical":
            probability += DEBT_PROBABILITY_INCREMENT * CRITICAL_DEBT_MULTIPLIER
        elif severity == "high":
            probability += DEBT_PROBABILITY_INCREMENT * HIGH_DEBT_MULTIPLIER
        else:
            probability += DEBT_PROBABILITY_INCREMENT

    # Add exception risk
    probability += len(active_exceptions) * EXCEPTION_RISK_INCREMENT

    # Cap at 95%
    probability = min(0.95, probability)

    return {
        "base_probability": BASE_INCIDENT_PROBABILITY,
        "debt_contribution": probability - BASE_INCIDENT_PROBABILITY - len(active_exceptions) * EXCEPTION_RISK_INCREMENT,
        "exception_contribution": len(active_exceptions) * EXCEPTION_RISK_INCREMENT,
        "total_probability": round(probability, 4),
        "open_debts": len(open_debts),
        "active_exceptions": len(active_exceptions)
    }


def calculate_expected_cost(probability_data: Dict, debts: List[Dict]) -> Dict:
    """Calculate expected cost based on incident probability."""
    prob = probability_data["total_probability"]

    # Count critical debts for cost estimation
    critical_count = sum(1 for d in debts if d.get("severity") == "critical" and d.get("status") == "open")

    # Expected cost = P(incident) * weighted average cost
    if critical_count > 0:
        avg_cost = (CRITICAL_INCIDENT_COST * critical_count + AVERAGE_INCIDENT_COST * (probability_data["open_debts"] - critical_count)) / max(1, probability_data["open_debts"])
    else:
        avg_cost = AVERAGE_INCIDENT_COST

    expected_cost = prob * avg_cost
    annualized_cost = expected_cost * 4  # Quarterly to annual

    return {
        "expected_quarterly_cost": round(expected_cost, 0),
        "annualized_expected_cost": round(annualized_cost, 0),
        "average_incident_cost": round(avg_cost, 0),
        "critical_debt_count": critical_count
    }


def calculate_investment_roi(probability_data: Dict, cost_data: Dict) -> Dict:
    """Calculate ROI for safety investments."""
    current_prob = probability_data["total_probability"]
    current_cost = cost_data["annualized_expected_cost"]

    # Model: Each $250k FTE reduces probability by ~3%
    investment_scenarios = []

    for fte in [1, 2, 3, 5]:
        investment = fte * SAFETY_FTE_COST
        prob_reduction = min(0.03 * fte, current_prob - BASE_INCIDENT_PROBABILITY)
        new_prob = max(BASE_INCIDENT_PROBABILITY, current_prob - prob_reduction)
        new_cost = new_prob * cost_data["average_incident_cost"] * 4

        risk_reduction = current_cost - new_cost
        roi = (risk_reduction - investment) / investment if investment > 0 else 0

        investment_scenarios.append({
            "fte_added": fte,
            "investment": investment,
            "probability_reduction": round(prob_reduction, 4),
            "new_probability": round(new_prob, 4),
            "risk_reduction": round(risk_reduction, 0),
            "net_benefit": round(risk_reduction - investment, 0),
            "roi_percent": round(roi * 100, 1)
        })

    # Find optimal investment
    positive_roi = [s for s in investment_scenarios if s["net_benefit"] > 0]
    optimal = max(positive_roi, key=lambda x: x["net_benefit"]) if positive_roi else investment_scenarios[0]

    return {
        "scenarios": investment_scenarios,
        "optimal_investment": optimal,
        "break_even_fte": next((s["fte_added"] for s in investment_scenarios if s["net_benefit"] >= 0), None)
    }


def generate_executive_summary(prob_data: Dict, cost_data: Dict, roi_data: Dict) -> str:
    """Generate executive-friendly summary."""
    optimal = roi_data["optimal_investment"]

    return f"""Based on current alignment debt ({prob_data['open_debts']} open) and active exceptions ({prob_data['active_exceptions']}),
the expected quarterly incident probability is {prob_data['total_probability']*100:.1f}%.

Expected annual risk exposure: ${cost_data['annualized_expected_cost']:,.0f}

Recommended investment: {optimal['fte_added']} FTE (${optimal['investment']:,.0f})
Expected risk reduction: ${optimal['risk_reduction']:,.0f}
Net benefit: ${optimal['net_benefit']:,.0f}
ROI: {optimal['roi_percent']:.0f}%"""


def generate_roi_model(debts: List[Dict], exceptions: List[Dict]) -> Dict:
    """Generate complete ROI model."""
    timestamp = datetime.now(timezone.utc).isoformat()

    prob_data = calculate_incident_probability(debts, exceptions)
    cost_data = calculate_expected_cost(prob_data, debts)
    roi_data = calculate_investment_roi(prob_data, cost_data)
    summary = generate_executive_summary(prob_data, cost_data, roi_data)

    return {
        "timestamp": timestamp,
        "model_version": "1.0",
        "parameters": {
            "base_incident_probability": BASE_INCIDENT_PROBABILITY,
            "debt_probability_increment": DEBT_PROBABILITY_INCREMENT,
            "average_incident_cost": AVERAGE_INCIDENT_COST,
            "critical_incident_cost": CRITICAL_INCIDENT_COST,
            "safety_fte_cost": SAFETY_FTE_COST
        },
        "probability_analysis": prob_data,
        "cost_analysis": cost_data,
        "investment_analysis": roi_data,
        "executive_summary": summary,
        "board_headline": f"${roi_data['optimal_investment']['investment']:,.0f} safety investment = {roi_data['optimal_investment']['probability_reduction']*100:.0f}% risk reduction (ROI: {roi_data['optimal_investment']['roi_percent']:.0f}%)"
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Safety ROI Model"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output JSON path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SAFETY ROI MODEL GENERATOR")
    print("=" * 60)

    debt_data = load_yaml(DEBT_PATH)
    debts = debt_data.get("ledger", debt_data.get("debts", []))
    exc_data = load_yaml(EXCEPTIONS_PATH)
    exceptions = exc_data.get("exceptions", [])

    model = generate_roi_model(debts, exceptions)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(model, f, indent=2)

    print(f"\n[OK] Safety ROI model generated: {args.output}")
    print("\n📊 Board Headline:")
    print(f"   {model['board_headline']}")
    print("\n💰 Executive Summary:")
    print(f"   {model['executive_summary']}")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
