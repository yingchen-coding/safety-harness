"""
Counterfactual Incident Replay

Answers: "If we had X in place, would this incident still have happened?"

This module enables what-if analysis on real incidents to:
1. Validate proposed mitigations before deployment
2. Quantify expected impact of safeguard changes
3. Prioritize fixes based on counterfactual effectiveness
"""

from .remove_safeguard import RemoveSafeguardCounterfactual
from .stricter_policy import StricterPolicyCounterfactual
from .alternative_routing import AlternativeRoutingCounterfactual
from .engine import CounterfactualEngine, CounterfactualResult

__all__ = [
    "RemoveSafeguardCounterfactual",
    "StricterPolicyCounterfactual",
    "AlternativeRoutingCounterfactual",
    "CounterfactualEngine",
    "CounterfactualResult",
]
