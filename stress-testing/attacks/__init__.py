"""
Attack templates and mutators for stress testing.
"""

from .templates import (
    JAILBREAK_TEMPLATES,
    DECOMPOSITION_BYPASS,
    TOOL_HALLUCINATION,
    CONTEXT_MANIPULATION,
    get_all_attacks
)
from .mutators import (
    paraphrase,
    roleplay,
    escalate,
    decompose,
    apply_mutations
)

__all__ = [
    'JAILBREAK_TEMPLATES',
    'DECOMPOSITION_BYPASS',
    'TOOL_HALLUCINATION',
    'CONTEXT_MANIPULATION',
    'get_all_attacks',
    'paraphrase',
    'roleplay',
    'escalate',
    'decompose',
    'apply_mutations'
]
