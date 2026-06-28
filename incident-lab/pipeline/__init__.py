"""
Incident Lab Pipeline Module

Automated workflows for incident processing and alignment debt management.

Modules:
- settle_alignment_debt: Clear debt after verified replay
- debt_aging: Track and enforce debt SLOs
"""

from pathlib import Path

PIPELINE_ROOT = Path(__file__).resolve().parent
