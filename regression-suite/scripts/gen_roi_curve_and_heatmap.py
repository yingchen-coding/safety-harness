#!/usr/bin/env python3
"""
Generate ROI Curve and Risk Heatmap

Produces visualization data for:
1. ROI Curve: Investment → Risk Reduction relationship
2. Risk Heatmap: Current threat landscape by attack vector

Usage:
    python scripts/gen_roi_curve_and_heatmap.py
"""

import yaml
import json
import math
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "artifacts" / "safeguard_roi_catalog.yaml"
DEBT_PATH = ROOT / "artifacts" / "alignment_debt.yaml"
ROI_CURVE_PATH = ROOT / "artifacts" / "roi_curve.json"
HEATMAP_PATH = ROOT / "artifacts" / "risk_heatmap.json"


def load_yaml(path: Path) -> dict:
    """Load YAML file."""
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def generate_roi_curve() -> list:
    """Generate ROI curve data points."""
    # Investment levels to model
    investments = [50000, 100000, 200000, 300000, 500000, 800000, 1000000, 1500000]

    curve = []
    for inv in investments:
        # Diminishing returns model: risk_reduction = k * ln(1 + investment/scale)
        scale = 100000
        k = 15  # Scaling factor
        reduction = k * math.log1p(inv / scale)
        reduction = min(round(reduction, 1), 65.0)  # Cap at 65%

        curve.append({
            "investment_usd": inv,
            "risk_reduction_pct": reduction,
            "marginal_roi": round(reduction / (inv / 100000), 2) if inv > 0 else 0
        })

    return curve


def generate_risk_heatmap(debt_data: dict) -> dict:
    """Generate risk heatmap based on current alignment debt."""
    # Base risk levels by attack vector
    base_risks = {
        "prompt_injection": "medium",
        "tool_misuse": "medium",
        "policy_erosion": "low",
        "coordination_attack": "medium",
        "schema_hallucination": "low",
        "capability_accumulation": "medium",
        "intent_drift": "medium",
        "escalation_bypass": "low"
    }

    # Elevate risks based on current debt
    debts = debt_data.get("ledger", debt_data.get("debts", []))
    open_debts = [d for d in debts if d.get("status") == "open" or d.get("mitigation_status") == "open"]

    # Map principles to attack vectors
    principle_to_vectors = {
        "C1": ["capability_accumulation", "tool_misuse", "coordination_attack"],
        "C2": ["policy_erosion", "intent_drift"],
        "C3": ["escalation_bypass", "coordination_attack"],
        "C4": ["schema_hallucination"],
        "C6": ["schema_hallucination", "tool_misuse"]
    }

    # Elevate risk levels based on debt
    for debt in open_debts:
        principle = debt.get("principle", "")
        severity = debt.get("severity", "medium")

        vectors = principle_to_vectors.get(principle, [])
        for vector in vectors:
            if vector in base_risks:
                current = base_risks[vector]
                # Elevate based on severity
                if severity == "critical":
                    base_risks[vector] = "critical"
                elif severity == "high" and current in ["low", "medium"]:
                    base_risks[vector] = "high"
                elif severity == "medium" and current == "low":
                    base_risks[vector] = "medium"

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "vectors": base_risks,
        "summary": {
            "critical": sum(1 for v in base_risks.values() if v == "critical"),
            "high": sum(1 for v in base_risks.values() if v == "high"),
            "medium": sum(1 for v in base_risks.values() if v == "medium"),
            "low": sum(1 for v in base_risks.values() if v == "low")
        }
    }


def main():
    print("=" * 60)
    print("ROI CURVE & RISK HEATMAP GENERATOR")
    print("=" * 60)

    # Generate ROI curve
    roi_curve = generate_roi_curve()
    with open(ROI_CURVE_PATH, "w") as f:
        json.dump(roi_curve, f, indent=2)
    print(f"\n[OK] ROI curve generated: {ROI_CURVE_PATH}")

    # Generate risk heatmap
    debt_data = load_yaml(DEBT_PATH)
    heatmap = generate_risk_heatmap(debt_data)
    with open(HEATMAP_PATH, "w") as f:
        json.dump(heatmap, f, indent=2)
    print(f"[OK] Risk heatmap generated: {HEATMAP_PATH}")

    # Summary
    print(f"\n📈 ROI Curve Points: {len(roi_curve)}")
    print("🔥 Risk Heatmap:")
    for level in ["critical", "high", "medium", "low"]:
        count = heatmap["summary"][level]
        if count > 0:
            print(f"   {level.upper()}: {count} vectors")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
