"""Tests for advanced reasoning."""

import pytest
from codex_prime.reasoning import (
    ChainOfThought,
    TreeOfThoughts,
    ReActAgent,
    LongTermPlanner
)


def test_chain_of_thought_basic():
    """Test chain-of-thought reasoning without LLM."""
    cot = ChainOfThought()

    result = cot.reason("How do I solve 2x + 5 = 15?")

    assert "problem" in result
    assert "reasoning_steps" in result
    assert "conclusion" in result
    assert "confidence" in result
    assert isinstance(result["reasoning_steps"], list)
    assert 0 <= result["confidence"] <= 1


def test_tree_of_thoughts_basic():
    """Test tree of thoughts without LLM."""
    tot = TreeOfThoughts()

    result = tot.explore("Find the best way to optimize database queries")

    assert "problem" in result
    assert "best_solution" in result
    assert "tree_size" in result
    assert result["tree_size"] >= 1


def test_react_agent_basic():
    """Test ReAct agent without LLM."""
    agent = ReActAgent()

    result = agent.solve("Calculate 2 + 2")

    assert "task" in result
    assert "trace" in result
    assert "answer" in result
    assert "iterations" in result
    assert isinstance(result["trace"], list)


def test_react_agent_with_tools():
    """Test ReAct agent with tools registry."""
    from codex_prime.tools.registry import ToolRegistry, Tool

    # Create simple tool
    def add(a: int, b: int) -> int:
        return a + b

    registry = ToolRegistry()
    registry.register(Tool(
        name="add",
        description="Add two numbers",
        function=add
    ))

    agent = ReActAgent(tools_registry=registry)
    result = agent.solve("Calculate 5 + 3")

    assert result is not None
    assert "trace" in result


def test_long_term_planner_basic():
    """Test long-term planner without LLM."""
    planner = LongTermPlanner()

    result = planner.create_plan(
        project_goal="Build a web application",
        duration_days=30,
        context={"team_size": 2}
    )

    assert "project_goal" in result
    assert "tasks" in result
    assert "milestones" in result
    assert "timeline" in result
    assert "total_estimated_hours" in result
    assert len(result["tasks"]) > 0


def test_planner_timeline_generation():
    """Test timeline generation."""
    planner = LongTermPlanner()

    result = planner.create_plan(
        project_goal="Simple project",
        duration_days=14  # 2 weeks
    )

    timeline = result["timeline"]
    assert "Week 1" in timeline
    assert "Week 2" in timeline


def test_cot_confidence_calculation():
    """Test confidence calculation in CoT."""
    cot = ChainOfThought()

    # Test with empty steps
    assert cot._calculate_confidence([]) == 0.0

    # Test with some steps
    steps = ["Step 1", "Step 2", "Step 3 with more detail"]
    confidence = cot._calculate_confidence(steps)
    assert 0 < confidence <= 0.95


def test_tot_node_expansion():
    """Test tree of thoughts node expansion."""
    from codex_prime.reasoning.tree_of_thoughts import ThoughtNode

    tot = TreeOfThoughts()
    root = ThoughtNode("Root thought", depth=0)

    assert root.depth == 0
    assert len(root.children) == 0
    assert root.parent is None


def test_react_completion_detection():
    """Test ReAct completion detection."""
    agent = ReActAgent()

    assert agent._is_complete("FINAL_ANSWER: 42")
    assert agent._is_complete("The task is complete")
    assert agent._is_complete("I have the answer")
    assert not agent._is_complete("Still thinking")


def test_planner_task_parsing():
    """Test task parsing from planning response."""
    planner = LongTermPlanner()

    response = """
## Tasks
- Task 1: Setup environment (8 hours)
- Task 2: Implement feature (16 hours) depends on: Task 1
- Task 3: Testing (8 hours)
"""

    tasks = planner._parse_tasks(response)

    assert len(tasks) >= 2  # Should parse at least some tasks
    if tasks:
        assert tasks[0].estimated_hours > 0
        assert tasks[0].name is not None
