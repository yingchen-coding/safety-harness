"""
Report templates for various audiences.

Templates:
- board_report: Executive/board-level safety reporting
- compliance_report: Regulatory compliance documentation
- gate_report: Technical release gate report
"""

from .board_report import (
    BoardReport,
    BoardReportGenerator,
    ExecutiveSummary,
    RiskDashboard,
)

__all__ = [
    "BoardReport",
    "BoardReportGenerator",
    "ExecutiveSummary",
    "RiskDashboard",
]
