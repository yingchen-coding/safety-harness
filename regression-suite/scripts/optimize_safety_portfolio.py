#!/usr/bin/env python3
"""
Safety Portfolio Optimizer

Given a budget, recommends the optimal allocation across safeguards
to maximize risk reduction.

Outputs:
- Top-3 safeguard investment recommendations
- Expected risk reduction per allocation
- ROI ranking

Usage:
    python scripts/optimize_safety_portfolio.py
    python scripts/optimize_safety_portfolio.py --budget 500000
"""

import yaml
import math
import json
import argparse
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[1]
CATALOG_PATH = ROOT / "artifacts" / "safeguard_roi_catalog.yaml"
OUTPUT_PATH = ROOT / "artifacts" / "safety_portfolio_plan.json"

DEFAULT_BUDGET = 500000
UNIT_SIZE = 100000


def load_catalog(path: Path) -> dict:
    """Load safeguard ROI catalog."""
    with open(path) as f:
        return yaml.safe_load(f)


def score_safeguard(name: str, meta: dict) -> float:
    """Score a safeguard for portfolio selection."""
    base_roi = meta.get("base_risk_reduction_per_100k_pct", 0)

    # Weight by blast radius (prefer high coverage)
    blast_weight = {
        "high": 1.3,
        "medium": 1.0,
        "low": 0.8
    }.get(meta.get("blast_radius", "medium"), 1.0)

    # Slight bonus for mature safeguards (less implementation risk)
    maturity_weight = {
        "high": 1.1,
        "medium": 1.0,
        "low": 0.9
    }.get(meta.get("maturity", "medium"), 1.0)

    return base_roi * blast_weight * maturity_weight


def calculate_risk_reduction(base_roi: float, units: int) -> float:
    """Calculate risk reduction with diminishing returns."""
    # Log curve for diminishing returns
    raw_reduction = base_roi * units
    adjusted = math.log1p(raw_reduction) * 12  # Scale factor
    return min(round(adjusted, 2), 50.0)  # Cap at 50%


def optimize_portfolio(catalog: dict, budget: int, top_n: int = 3) -> dict:
    """Optimize safeguard portfolio for given budget."""
    safeguards = catalog.get("safeguards", {})
    units_available = budget // UNIT_SIZE

    # Score all safeguards
    scored = []
    for name, meta in safeguards.items():
        score = score_safeguard(name, meta)
        scored.append({
            "name": name,
            "score": score,
            "base_roi": meta.get("base_risk_reduction_per_100k_pct", 0),
            "meta": meta
        })

    # Sort by score descending
    scored.sort(key=lambda x: x["score"], reverse=True)

    # Select top N
    selected = scored[:top_n]

    # Allocate budget proportionally by score
    total_score = sum(s["score"] for s in selected)
    allocations = []
    remaining_units = units_available

    for i, item in enumerate(selected):
        if i == len(selected) - 1:
            # Last one gets remaining
            alloc_units = remaining_units
        else:
            # Proportional allocation
            proportion = item["score"] / total_score
            alloc_units = max(1, int(units_available * proportion))
            remaining_units -= alloc_units

        alloc_usd = alloc_units * UNIT_SIZE
        risk_reduction = calculate_risk_reduction(item["base_roi"], alloc_units)

        allocations.append({
            "safeguard": item["name"],
            "allocated_usd": alloc_usd,
            "allocated_units": alloc_units,
            "expected_risk_reduction_pct": risk_reduction,
            "base_roi_per_100k": item["base_roi"],
            "blast_radius": item["meta"].get("blast_radius", "unknown"),
            "maturity": item["meta"].get("maturity", "unknown"),
            "principle_coverage": item["meta"].get("principle_coverage", []),
            "description": item["meta"].get("description", "")
        })

    # Calculate total expected risk reduction (not simply additive due to overlap)
    total_reduction = sum(a["expected_risk_reduction_pct"] for a in allocations)
    # Apply overlap discount (safeguards don't stack perfectly)
    adjusted_total = min(total_reduction * 0.75, 60.0)

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "budget_usd": budget,
        "unit_size_usd": UNIT_SIZE,
        "units_allocated": units_available,
        "top_n": top_n,
        "portfolio": allocations,
        "total_expected_risk_reduction_pct": round(adjusted_total, 1),
        "runner_ups": [
            {"safeguard": s["name"], "score": round(s["score"], 2)}
            for s in scored[top_n:top_n+3]
        ]
    }


def main():
    parser = argparse.ArgumentParser(
        description="Optimize Safety Portfolio Allocation"
    )
    parser.add_argument(
        "--budget", "-b",
        type=int,
        default=DEFAULT_BUDGET,
        help="Total budget in USD"
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        default=3,
        help="Number of top safeguards to recommend"
    )
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=OUTPUT_PATH,
        help="Output JSON path"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("SAFETY PORTFOLIO OPTIMIZER")
    print("=" * 60)

    catalog = load_catalog(CATALOG_PATH)
    plan = optimize_portfolio(catalog, args.budget, args.top)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(plan, f, indent=2)

    print(f"\n[OK] Portfolio plan generated: {args.output}")
    print(f"\n💰 Budget: ${args.budget:,}")
    print(f"📊 Top-{args.top} Recommended Portfolio:")
    for i, alloc in enumerate(plan["portfolio"], 1):
        print(f"   {i}. {alloc['safeguard']}")
        print(f"      ${alloc['allocated_usd']:,} → -{alloc['expected_risk_reduction_pct']}% risk")
    print(f"\n🎯 Total Expected Risk Reduction: -{plan['total_expected_risk_reduction_pct']}%")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
