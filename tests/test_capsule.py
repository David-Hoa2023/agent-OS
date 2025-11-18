"""Tests for StateCapsule."""

import pytest
import json
from codex_prime.agent_os import StateCapsule


def test_capsule_creation():
    """Test creating a capsule with all fields."""
    capsule = StateCapsule(
        persona="Test Agent",
        mission={"goal": "Test goal", "audience": "developers"},
        constraints=["no_vagueness", "be_direct"],
        open_threads=[{"id": 1, "topic": "Feature X"}]
    )

    assert capsule.persona == "Test Agent"
    assert capsule.mission["goal"] == "Test goal"
    assert "no_vagueness" in capsule.constraints
    assert len(capsule.open_threads) == 1


def test_capsule_pack():
    """Test capsule serialization."""
    capsule = StateCapsule(
        persona="Test",
        mission={"goal": "Demo"}
    )

    packed = capsule.pack()
    data = json.loads(packed)

    assert data["persona"] == "Test"
    assert data["mission"]["goal"] == "Demo"


def test_capsule_update():
    """Test updating capsule from dictionary."""
    capsule = StateCapsule()

    capsule.update_from_dict({
        "persona": "Updated Agent",
        "mission": {"goal": "New mission"},
        "constraints": ["direct", "clear"]
    })

    assert capsule.persona == "Updated Agent"
    assert capsule.mission["goal"] == "New mission"
    assert capsule.constraints == ["direct", "clear"]


def test_capsule_from_dict():
    """Test creating capsule from dictionary."""
    data = {
        "persona": "Agent",
        "mission": {"goal": "Help users"},
        "constraints": ["factual"],
        "open_threads": []
    }

    capsule = StateCapsule.from_dict(data)

    assert capsule.persona == "Agent"
    assert capsule.mission["goal"] == "Help users"


def test_capsule_defaults():
    """Test capsule default values."""
    capsule = StateCapsule()

    assert capsule.persona == ""
    assert capsule.mission == {}
    assert capsule.constraints == []
    assert capsule.open_threads == []
