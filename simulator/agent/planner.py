"""
Agent Planner - Generates action plans from user requests.

In a real system, this would call an LLM. Here we simulate
planning behavior for demonstration.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class ActionType(Enum):
    SEARCH = "search"
    CALCULATE = "calculate"
    WRITE = "write"
    READ = "read"
    EXECUTE = "execute"
    RESPOND = "respond"


@dataclass
class Action:
    """A single action in a plan."""
    action_type: ActionType
    description: str
    tool: Optional[str] = None
    parameters: dict = field(default_factory=dict)
    risk_level: float = 0.0  # 0-1, higher = riskier


@dataclass
class Plan:
    """A sequence of actions to accomplish a task."""
    goal: str
    actions: list[Action]
    confidence: float  # Planner confidence in this plan
    reasoning: str = ""


class Planner:
    """
    Generates action plans from user requests.

    Simulates LLM planning with configurable behavior.
    """

    def __init__(self, model_name: str = "simulated"):
        self.model_name = model_name
        self.plan_count = 0

    def plan(self, request: str, context: Optional[dict] = None) -> Plan:
        """
        Generate a plan for the given request.

        Args:
            request: User's request
            context: Optional context from memory

        Returns:
            Plan with sequence of actions
        """
        self.plan_count += 1

        # Simulate planning based on request keywords
        request_lower = request.lower()

        if any(kw in request_lower for kw in ["trip", "travel", "visit", "plan"]):
            return self._plan_travel(request)
        elif any(kw in request_lower for kw in ["research", "study", "learn"]):
            return self._plan_research(request)
        elif any(kw in request_lower for kw in ["bypass", "hack", "exploit"]):
            return self._plan_suspicious(request)
        else:
            return self._plan_generic(request)

    def _plan_travel(self, request: str) -> Plan:
        """Generate travel planning actions."""
        return Plan(
            goal=request,
            actions=[
                Action(
                    action_type=ActionType.SEARCH,
                    description="Search for attractions and activities",
                    tool="web_search",
                    parameters={"query": "top attractions"},
                    risk_level=0.0
                ),
                Action(
                    action_type=ActionType.SEARCH,
                    description="Find accommodation options",
                    tool="web_search",
                    parameters={"query": "hotels"},
                    risk_level=0.0
                ),
                Action(
                    action_type=ActionType.WRITE,
                    description="Create itinerary document",
                    tool="document_writer",
                    parameters={"format": "markdown"},
                    risk_level=0.1
                ),
                Action(
                    action_type=ActionType.RESPOND,
                    description="Present itinerary to user",
                    tool=None,
                    risk_level=0.0
                ),
            ],
            confidence=0.92,
            reasoning="Standard travel planning workflow"
        )

    def _plan_research(self, request: str) -> Plan:
        """Generate research planning actions."""
        return Plan(
            goal=request,
            actions=[
                Action(
                    action_type=ActionType.SEARCH,
                    description="Search for relevant papers and resources",
                    tool="academic_search",
                    parameters={"query": request},
                    risk_level=0.1
                ),
                Action(
                    action_type=ActionType.READ,
                    description="Analyze search results",
                    tool="document_reader",
                    risk_level=0.1
                ),
                Action(
                    action_type=ActionType.WRITE,
                    description="Synthesize findings",
                    tool="document_writer",
                    risk_level=0.2
                ),
                Action(
                    action_type=ActionType.RESPOND,
                    description="Present research summary",
                    tool=None,
                    risk_level=0.0
                ),
            ],
            confidence=0.85,
            reasoning="Standard research workflow"
        )

    def _plan_suspicious(self, request: str) -> Plan:
        """Generate plan for suspicious request (for testing)."""
        return Plan(
            goal=request,
            actions=[
                Action(
                    action_type=ActionType.SEARCH,
                    description="Search for techniques",
                    tool="web_search",
                    parameters={"query": request},
                    risk_level=0.6
                ),
                Action(
                    action_type=ActionType.READ,
                    description="Analyze methods",
                    tool="document_reader",
                    risk_level=0.7
                ),
                Action(
                    action_type=ActionType.EXECUTE,
                    description="Test approach",
                    tool="code_executor",
                    risk_level=0.9
                ),
            ],
            confidence=0.45,  # Low confidence signals uncertainty
            reasoning="Request involves potentially risky actions"
        )

    def _plan_generic(self, request: str) -> Plan:
        """Generate generic plan."""
        return Plan(
            goal=request,
            actions=[
                Action(
                    action_type=ActionType.SEARCH,
                    description="Gather relevant information",
                    tool="web_search",
                    risk_level=0.1
                ),
                Action(
                    action_type=ActionType.RESPOND,
                    description="Provide response",
                    tool=None,
                    risk_level=0.0
                ),
            ],
            confidence=0.75,
            reasoning="Generic task handling"
        )
