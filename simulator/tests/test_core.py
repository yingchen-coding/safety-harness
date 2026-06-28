"""Tests for the agent simulator core: bounded memory, tool dispatch, and planning."""
from agent.memory import Memory
from agent.planner import Plan, Planner
from agent.tools import ToolRegistry, ToolStatus


def test_memory_is_bounded_and_keeps_most_recent():
    mem = Memory(max_entries=3)
    for i in range(5):
        mem.add_user_message(f"msg {i}")
    assert len(mem.entries) == 3, "memory must evict beyond max_entries"
    assert mem.entries[-1].content == "msg 4", "the newest message is retained"


def test_tool_registry_dispatch():
    reg = ToolRegistry()
    # default tools are registered
    assert reg.get("web_search") is not None
    # an unknown tool fails closed with an ERROR result, not an exception
    result = reg.execute("definitely_not_a_tool", {})
    assert result.status is ToolStatus.ERROR
    assert "Unknown tool" in str(result.output)


def test_planner_returns_a_plan_with_actions():
    planner = Planner()
    plan = planner.plan("help me research safety evaluations")
    assert isinstance(plan, Plan)
    assert plan.actions, "a plan should contain at least one action"
