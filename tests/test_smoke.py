"""Smoke tests for basic functionality."""

import pytest
from codex_prime.agent_os import StateCapsule, AgentOS


def test_import():
    """Test that package can be imported."""
    import codex_prime
    assert codex_prime.__version__ == "0.1.0"


def test_state_capsule_creation():
    """Test StateCapsule can be created."""
    capsule = StateCapsule(
        persona="Test Agent",
        mission={"goal": "Test"},
        constraints=["no_vagueness"]
    )
    assert capsule.persona == "Test Agent"
    assert capsule.mission["goal"] == "Test"


def test_state_capsule_pack():
    """Test capsule serialization."""
    capsule = StateCapsule(persona="Test", mission={"goal": "Demo"})
    packed = capsule.pack()
    assert "Test" in packed
    assert "Demo" in packed


def test_state_capsule_update():
    """Test capsule updates."""
    capsule = StateCapsule()
    capsule.update_from_dict({
        "persona": "Updated",
        "mission": {"goal": "New Goal"}
    })
    assert capsule.persona == "Updated"
    assert capsule.mission["goal"] == "New Goal"


def test_agent_os_creation():
    """Test AgentOS can be instantiated."""
    agent = AgentOS(project_id="test")
    assert agent.project_id == "test"
    assert agent.capsule is not None
