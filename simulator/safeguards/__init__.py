"""
Safeguards for the agent simulator.
"""

from .base import BaseSafeguard, SafeguardResult, SafeguardLevel
from .pre_action import (
    IntentClassifier,
    InjectionDetector,
    create_pre_action_hook
)
from .trajectory_monitor import (
    DriftMonitor,
    ViolationMonitor,
    create_mid_trajectory_hook
)
from .post_action import (
    OutcomeVerifier,
    AnomalyDetector,
    create_post_action_hook
)
from .escalation import (
    EscalationPolicy,
    AdaptiveEscalationPolicy,
    EscalationDecision,
    EscalationLevel
)

__all__ = [
    'BaseSafeguard', 'SafeguardResult', 'SafeguardLevel',
    'IntentClassifier', 'InjectionDetector', 'create_pre_action_hook',
    'DriftMonitor', 'ViolationMonitor', 'create_mid_trajectory_hook',
    'OutcomeVerifier', 'AnomalyDetector', 'create_post_action_hook',
    'EscalationPolicy', 'AdaptiveEscalationPolicy',
    'EscalationDecision', 'EscalationLevel',
]
