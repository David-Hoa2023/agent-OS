"""Tests for multi-agent orchestration."""

import pytest
import time
from codex_prime.orchestration import Coordinator, Workflow, WorkflowStep, MessageBus, Message
from codex_prime.orchestration.workflow import StepStatus


# Mock agent for testing
class MockAgent:
    """Mock agent for testing."""

    def __init__(self, name: str, delay: float = 0.0, should_fail: bool = False):
        self.name = name
        self.delay = delay
        self.should_fail = should_fail
        self.call_count = 0

    def process(self, task: str, context=None):
        self.call_count += 1
        if self.delay > 0:
            time.sleep(self.delay)
        if self.should_fail:
            raise Exception(f"{self.name} failed")
        return {"agent": self.name, "task": task, "result": "success"}


def test_message_bus_publish():
    """Test publishing messages."""
    bus = MessageBus()

    message = Message(
        from_agent="agent1",
        to_agent="agent2",
        message_type="task",
        content={"data": "test"}
    )

    bus.publish(message)

    messages = bus.get_messages(agent_id="agent2")
    assert len(messages) == 1
    assert messages[0].from_agent == "agent1"


def test_message_bus_subscribe():
    """Test subscribing to messages."""
    bus = MessageBus()
    received = []

    def callback(msg):
        received.append(msg)

    bus.subscribe("agent1", callback)

    message = Message(from_agent="agent2", to_agent="agent1", content={})
    bus.publish(message)

    assert len(received) == 1
    assert received[0].to_agent == "agent1"


def test_message_bus_broadcast():
    """Test broadcasting messages."""
    bus = MessageBus()
    received1 = []
    received2 = []

    bus.subscribe("agent1", lambda msg: received1.append(msg))
    bus.subscribe("agent2", lambda msg: received2.append(msg))

    # Broadcast (no specific recipient)
    message = Message(from_agent="coordinator", to_agent=None, content={})
    bus.publish(message)

    assert len(received1) == 1
    assert len(received2) == 1


def test_workflow_creation():
    """Test creating a workflow."""
    workflow = Workflow(workflow_id="wf1", name="Test Workflow")

    assert workflow.workflow_id == "wf1"
    assert workflow.name == "Test Workflow"
    assert len(workflow.steps) == 0


def test_workflow_add_step():
    """Test adding steps to workflow."""
    workflow = Workflow(workflow_id="wf1", name="Test")

    step1 = workflow.add_step("step1", "agent1", "Task 1")
    step2 = workflow.add_step("step2", "agent2", "Task 2", depends_on=["step1"])

    assert len(workflow.steps) == 2
    assert step2.depends_on == ["step1"]


def test_workflow_get_ready_steps():
    """Test getting ready steps."""
    workflow = Workflow(workflow_id="wf1", name="Test")

    step1 = workflow.add_step("step1", "agent1", "Task 1")
    step2 = workflow.add_step("step2", "agent2", "Task 2", depends_on=["step1"])
    step3 = workflow.add_step("step3", "agent3", "Task 3")

    # Initially, step1 and step3 should be ready (no dependencies)
    ready = workflow.get_ready_steps()
    assert len(ready) == 2
    assert step1 in ready
    assert step3 in ready

    # Mark step1 as completed
    step1.status = StepStatus.COMPLETED

    # Now step2 should be ready
    ready = workflow.get_ready_steps()
    assert len(ready) == 2  # step2 and step3
    assert step2 in ready


def test_workflow_progress():
    """Test workflow progress tracking."""
    workflow = Workflow(workflow_id="wf1", name="Test")

    workflow.add_step("step1", "agent1", "Task 1")
    workflow.add_step("step2", "agent2", "Task 2")
    workflow.add_step("step3", "agent3", "Task 3")

    progress = workflow.get_progress()
    assert progress['total'] == 3
    assert progress['pending'] == 3
    assert progress['completed'] == 0

    workflow.steps[0].status = StepStatus.COMPLETED
    workflow.steps[1].status = StepStatus.RUNNING

    progress = workflow.get_progress()
    assert progress['completed'] == 1
    assert progress['running'] == 1
    assert progress['pending'] == 1


def test_coordinator_register_agent():
    """Test registering agents."""
    coordinator = Coordinator()
    agent = MockAgent("test_agent")

    coordinator.register_agent("test_agent", agent)

    assert "test_agent" in coordinator.agents
    assert coordinator.agents["test_agent"] == agent


def test_coordinator_create_workflow():
    """Test creating workflow through coordinator."""
    coordinator = Coordinator()

    workflow = coordinator.create_workflow("wf1", "Test Workflow")

    assert workflow.workflow_id == "wf1"
    assert "wf1" in coordinator.active_workflows


def test_coordinator_execute_simple_workflow():
    """Test executing a simple workflow."""
    coordinator = Coordinator()

    # Register agents
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    coordinator.register_agent("agent1", agent1)
    coordinator.register_agent("agent2", agent2)

    # Create workflow
    workflow = coordinator.create_workflow("wf1", "Simple Workflow")
    workflow.add_step("step1", "agent1", "Do task 1")
    workflow.add_step("step2", "agent2", "Do task 2")

    # Execute
    result = coordinator.execute_workflow(workflow)

    assert result['status'] == 'completed'
    assert agent1.call_count == 1
    assert agent2.call_count == 1


def test_coordinator_execute_with_dependencies():
    """Test executing workflow with dependencies."""
    coordinator = Coordinator()

    # Register agents
    agent1 = MockAgent("agent1")
    agent2 = MockAgent("agent2")
    coordinator.register_agent("agent1", agent1)
    coordinator.register_agent("agent2", agent2)

    # Create workflow with dependencies
    workflow = coordinator.create_workflow("wf1", "Dependent Workflow")
    workflow.add_step("step1", "agent1", "Task 1")
    workflow.add_step("step2", "agent2", "Task 2", depends_on=["step1"])

    # Execute
    result = coordinator.execute_workflow(workflow)

    assert result['status'] == 'completed'
    assert workflow.steps[0].status == StepStatus.COMPLETED
    assert workflow.steps[1].status == StepStatus.COMPLETED


def test_coordinator_handle_failure():
    """Test handling workflow step failure."""
    coordinator = Coordinator()

    # Register failing agent
    failing_agent = MockAgent("failing", should_fail=True)
    normal_agent = MockAgent("normal")
    coordinator.register_agent("failing", failing_agent)
    coordinator.register_agent("normal", normal_agent)

    # Create workflow
    workflow = coordinator.create_workflow("wf1", "Failing Workflow")
    workflow.add_step("step1", "failing", "Fail this")
    workflow.add_step("step2", "normal", "Normal task", depends_on=["step1"])

    # Execute
    result = coordinator.execute_workflow(workflow)

    assert result['status'] == 'failed'
    assert workflow.steps[0].status == StepStatus.FAILED
    # step2 should not execute because step1 failed
    assert workflow.steps[1].status == StepStatus.PENDING


def test_coordinator_parallel_execution():
    """Test parallel step execution."""
    coordinator = Coordinator()

    # Register agents with delays
    agent1 = MockAgent("agent1", delay=0.1)
    agent2 = MockAgent("agent2", delay=0.1)
    coordinator.register_agent("agent1", agent1)
    coordinator.register_agent("agent2", agent2)

    # Create workflow with parallel steps
    workflow = coordinator.create_workflow("wf1", "Parallel Workflow")
    workflow.add_step("step1", "agent1", "Task 1")
    workflow.add_step("step2", "agent2", "Task 2")  # No dependency, can run in parallel

    start_time = time.time()
    result = coordinator.execute_workflow(workflow, max_parallel=2)
    duration = time.time() - start_time

    assert result['status'] == 'completed'
    # Should take ~0.1s (parallel) not ~0.2s (sequential)
    assert duration < 0.3


def test_workflow_to_dict():
    """Test workflow serialization."""
    workflow = Workflow(workflow_id="wf1", name="Test")
    workflow.add_step("step1", "agent1", "Task 1")

    data = workflow.to_dict()

    assert data['workflow_id'] == "wf1"
    assert data['name'] == "Test"
    assert len(data['steps']) == 1
    assert 'progress' in data
