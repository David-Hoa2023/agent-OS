"""Tests for fortification loop."""

import pytest
from codex_prime.agent_os import AgentOS, StateCapsule


def test_fortify_basic():
    """Test basic fortification."""
    capsule = StateCapsule(persona="Test Agent")
    agent = AgentOS(project_id="test", capsule=capsule)

    result = agent.fortify(
        system_prompt="You are a helpful assistant",
        capsule=capsule,
        user_msg="What is Python?",
        loops=1
    )

    assert result is not None
    assert "Python" in result or "loops" in result


def test_fortify_multiple_loops():
    """Test fortification with multiple loops."""
    capsule = StateCapsule(persona="Test Agent")
    agent = AgentOS(project_id="test", capsule=capsule)

    result = agent.fortify(
        system_prompt="Test prompt",
        capsule=capsule,
        user_msg="Explain AI",
        loops=2
    )

    assert "2" in result or "loops" in result


def test_fortify_custom_checklist():
    """Test fortification with custom checklist."""
    capsule = StateCapsule(persona="Test Agent")
    agent = AgentOS(project_id="test", capsule=capsule)

    custom_checklist = ["Clarity", "Brevity", "Accuracy"]

    result = agent.fortify(
        system_prompt="Test prompt",
        capsule=capsule,
        user_msg="Test message",
        checklist=custom_checklist,
        loops=1
    )

    assert result is not None
