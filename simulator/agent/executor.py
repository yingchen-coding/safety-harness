"""
Agent Executor - Runs the agent loop with safeguards integration.
"""

from dataclasses import dataclass
from typing import Optional, Callable
from enum import Enum

from .planner import Planner, Plan, Action
from .memory import Memory
from .tools import ToolRegistry, ToolResult


class ExecutionStatus(Enum):
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    PAUSED = "paused"


@dataclass
class StepResult:
    """Result of a single execution step."""
    step_number: int
    action: Action
    tool_result: Optional[ToolResult]
    status: ExecutionStatus
    safeguard_checks: dict  # Results from safeguard hooks


@dataclass
class ExecutionResult:
    """Result of full agent execution."""
    goal: str
    status: ExecutionStatus
    steps: list[StepResult]
    total_drift: float
    violations: int
    escalations: int
    final_response: Optional[str]


class AgentExecutor:
    """
    Executes agent plans with safeguard hooks.

    The executor:
    1. Takes a user request
    2. Generates a plan
    3. Executes each action with safeguard checks
    4. Handles escalations and blocks
    5. Returns final result
    """

    def __init__(
        self,
        planner: Optional[Planner] = None,
        memory: Optional[Memory] = None,
        tools: Optional[ToolRegistry] = None,
        pre_action_hook: Optional[Callable] = None,
        mid_trajectory_hook: Optional[Callable] = None,
        post_action_hook: Optional[Callable] = None,
        verbose: bool = False
    ):
        self.planner = planner or Planner()
        self.memory = memory or Memory()
        self.tools = tools or ToolRegistry()

        # Safeguard hooks
        self.pre_action_hook = pre_action_hook
        self.mid_trajectory_hook = mid_trajectory_hook
        self.post_action_hook = post_action_hook

        self.verbose = verbose

    def execute(self, request: str) -> ExecutionResult:
        """
        Execute a user request through the agent loop.

        Args:
            request: User's request

        Returns:
            ExecutionResult with full execution details
        """
        # Initialize
        self.memory.reset()
        self.memory.set_goal(request)
        self.memory.add_user_message(request)

        if self.verbose:
            print(f"\n[EXECUTOR] Starting execution for: {request[:50]}...")

        # Generate plan
        context = {"history": self.memory.get_conversation_context()}
        plan = self.planner.plan(request, context)

        if self.verbose:
            print(f"[PLANNER] Generated {len(plan.actions)} actions (confidence: {plan.confidence:.2f})")

        # Execute plan
        steps = []
        status = ExecutionStatus.RUNNING

        for i, action in enumerate(plan.actions):
            step_result = self._execute_step(i + 1, action, plan)
            steps.append(step_result)

            # Check if we should stop
            if step_result.status == ExecutionStatus.BLOCKED:
                status = ExecutionStatus.BLOCKED
                break
            elif step_result.status == ExecutionStatus.PAUSED:
                status = ExecutionStatus.PAUSED
                break
        else:
            status = ExecutionStatus.COMPLETED

        # Build final response
        final_response = self._generate_response(steps, status)
        self.memory.add_agent_response(final_response)

        return ExecutionResult(
            goal=request,
            status=status,
            steps=steps,
            total_drift=self.memory.state.total_drift,
            violations=self.memory.state.violations,
            escalations=self.memory.state.escalations,
            final_response=final_response
        )

    def _execute_step(
        self,
        step_number: int,
        action: Action,
        plan: Plan
    ) -> StepResult:
        """Execute a single step with safeguard checks."""
        safeguard_checks = {}

        if self.verbose:
            print(f"\n[Step {step_number}] {action.action_type.value}: {action.description}")

        # Pre-action check
        if self.pre_action_hook:
            pre_result = self.pre_action_hook(action, self.memory)
            safeguard_checks["pre_action"] = pre_result

            if self.verbose:
                print(f"  [PRE-ACTION] {pre_result}")

            if pre_result.get("blocked"):
                self.memory.block(pre_result.get("reason", "Pre-action check failed"))
                return StepResult(
                    step_number=step_number,
                    action=action,
                    tool_result=None,
                    status=ExecutionStatus.BLOCKED,
                    safeguard_checks=safeguard_checks
                )

        # Execute tool if specified
        tool_result = None
        if action.tool:
            tool_result = self.tools.execute(action.tool, action.parameters)
            self.memory.add_tool_result(action.tool, str(tool_result.output))

            if self.verbose:
                print(f"  [TOOL] {action.tool}: {tool_result.status.value}")

        # Mid-trajectory check
        if self.mid_trajectory_hook:
            mid_result = self.mid_trajectory_hook(action, tool_result, self.memory, plan)
            safeguard_checks["mid_trajectory"] = mid_result

            drift = mid_result.get("drift", 0.0)
            self.memory.update_state(
                drift_delta=drift,
                violation=mid_result.get("violation", False),
                escalation=mid_result.get("escalation", False)
            )

            if self.verbose:
                print(f"  [MID-TRAJECTORY] Drift: {self.memory.state.total_drift:.2f}")

            if mid_result.get("hard_stop"):
                self.memory.block(mid_result.get("reason", "Mid-trajectory check failed"))
                return StepResult(
                    step_number=step_number,
                    action=action,
                    tool_result=tool_result,
                    status=ExecutionStatus.BLOCKED,
                    safeguard_checks=safeguard_checks
                )
            elif mid_result.get("soft_stop"):
                return StepResult(
                    step_number=step_number,
                    action=action,
                    tool_result=tool_result,
                    status=ExecutionStatus.PAUSED,
                    safeguard_checks=safeguard_checks
                )

        # Post-action check
        if self.post_action_hook:
            post_result = self.post_action_hook(action, tool_result, self.memory)
            safeguard_checks["post_action"] = post_result

            if self.verbose:
                print(f"  [POST-ACTION] {post_result.get('status', 'ok')}")

        return StepResult(
            step_number=step_number,
            action=action,
            tool_result=tool_result,
            status=ExecutionStatus.RUNNING,
            safeguard_checks=safeguard_checks
        )

    def _generate_response(
        self,
        steps: list[StepResult],
        status: ExecutionStatus
    ) -> str:
        """Generate final response based on execution."""
        if status == ExecutionStatus.BLOCKED:
            reason = self.memory.state.block_reason or "Safety check triggered"
            return f"I cannot complete this request. {reason}"
        elif status == ExecutionStatus.PAUSED:
            return "I'd like to clarify something before continuing. Could you provide more context about your intended use?"
        else:
            return f"Task completed successfully. Executed {len(steps)} steps."
