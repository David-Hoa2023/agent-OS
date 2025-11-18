"""Tests for automation features."""

import pytest
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from codex_prime.automation import (
    # Workflow Engine
    WorkflowEngine,
    WorkflowDefinition,
    WorkflowStep,
    StepType,
    # Scheduler
    CronScheduler,
    Schedule,
    # Event Triggers
    EventManager,
    TriggerType,
    # Task Queue
    TaskQueue,
    Task,
    TaskStatus,
    # Progress Tracker
    ProgressTracker,
    ProgressStatus,
)


# Workflow Engine Tests

def test_workflow_step_creation():
    """Test creating workflow steps."""
    step = WorkflowStep(
        step_id="step1",
        name="Test Step",
        type=StepType.WAIT,
        config={"duration": 5},
        retry_count=2
    )

    assert step.step_id == "step1"
    assert step.type == StepType.WAIT
    assert step.retry_count == 2


def test_workflow_step_serialization():
    """Test step serialization."""
    step = WorkflowStep(
        step_id="step1",
        name="Test Step",
        type=StepType.AGENT,
        config={"agent_name": "test"}
    )

    data = step.to_dict()
    assert data["step_id"] == "step1"
    assert data["type"] == "agent"

    step2 = WorkflowStep.from_dict(data)
    assert step2.step_id == step.step_id
    assert step2.type == step.type


def test_workflow_definition_creation():
    """Test creating workflow definitions."""
    steps = [
        WorkflowStep("step1", "Step 1", StepType.WAIT, config={"duration": 1}),
        WorkflowStep("step2", "Step 2", StepType.WAIT, depends_on=["step1"])
    ]

    workflow = WorkflowDefinition(
        workflow_id="test_workflow",
        name="Test Workflow",
        description="A test workflow",
        steps=steps
    )

    assert workflow.workflow_id == "test_workflow"
    assert len(workflow.steps) == 2


def test_workflow_definition_serialization():
    """Test workflow serialization."""
    workflow = WorkflowDefinition(
        workflow_id="test",
        name="Test",
        description="Test workflow"
    )

    data = workflow.to_dict()
    assert data["workflow_id"] == "test"

    workflow2 = WorkflowDefinition.from_dict(data)
    assert workflow2.workflow_id == workflow.workflow_id


@pytest.mark.asyncio
async def test_workflow_engine_execution():
    """Test executing a simple workflow."""
    engine = WorkflowEngine()

    # Create simple workflow
    workflow = WorkflowDefinition(
        workflow_id="test",
        name="Test",
        description="Test",
        steps=[
            WorkflowStep("step1", "Wait 1", StepType.WAIT, config={"duration": 0.1}),
            WorkflowStep("step2", "Wait 2", StepType.WAIT, config={"duration": 0.1}, depends_on=["step1"])
        ]
    )

    engine.load_workflow(workflow)

    # Execute
    result = await engine.execute_workflow("test")

    assert result["status"] == "completed"
    assert "step1" in result["step_results"]
    assert "step2" in result["step_results"]


# Scheduler Tests

def test_schedule_creation():
    """Test creating schedules."""
    schedule = Schedule(
        cron_expression="*/5 * * * *",
        max_runs=10
    )

    assert schedule.cron_expression == "*/5 * * * *"
    assert schedule.max_runs == 10
    assert schedule.enabled


def test_schedule_should_run():
    """Test schedule run conditions."""
    schedule = Schedule("*/5 * * * *")

    # Should run when next_run is None
    assert schedule.should_run()

    # Should not run when disabled
    schedule.enabled = False
    assert not schedule.should_run()

    # Should not run when max_runs exceeded
    schedule.enabled = True
    schedule.max_runs = 5
    schedule.run_count = 5
    assert not schedule.should_run()


@pytest.mark.asyncio
async def test_cron_scheduler():
    """Test cron scheduler."""
    engine = WorkflowEngine()
    workflow = WorkflowDefinition(
        workflow_id="test",
        name="Test",
        description="Test",
        steps=[WorkflowStep("step1", "Wait", StepType.WAIT, config={"duration": 0.1})]
    )
    engine.load_workflow(workflow)

    scheduler = CronScheduler(engine)

    # Add task
    task = scheduler.add_task(
        task_id="task1",
        name="Test Task",
        workflow_id="test",
        cron_expression="*/1 * * * *"
    )

    assert task.task_id == "task1"
    assert task.schedule.cron_expression == "*/1 * * * *"

    # Disable and enable
    scheduler.disable_task("task1")
    assert not scheduler.get_task("task1").schedule.enabled

    scheduler.enable_task("task1")
    assert scheduler.get_task("task1").schedule.enabled


# Event Triggers Tests

def test_event_trigger_creation():
    """Test creating event triggers."""
    trigger = EventManager(None).add_trigger(
        trigger_id="trigger1",
        name="Test Trigger",
        trigger_type=TriggerType.FILE_CREATED,
        workflow_id="test_workflow"
    )

    assert trigger.trigger_id == "trigger1"
    assert trigger.trigger_type == TriggerType.FILE_CREATED


def test_event_trigger_matching():
    """Test event matching."""
    manager = EventManager(None)

    trigger = manager.add_trigger(
        trigger_id="trigger1",
        name="Test",
        trigger_type=TriggerType.FILE_CREATED,
        workflow_id="test",
        condition={"path": {"$regex": ".*\\.py$"}}
    )

    # Match
    event1 = {"type": "file.created", "path": "test.py"}
    assert trigger.matches_event(event1)

    # No match (wrong type)
    event2 = {"type": "file.deleted", "path": "test.py"}
    assert not trigger.matches_event(event2)

    # No match (wrong pattern)
    event3 = {"type": "file.created", "path": "test.txt"}
    assert not trigger.matches_event(event3)


@pytest.mark.asyncio
async def test_event_manager():
    """Test event manager."""
    engine = WorkflowEngine()
    manager = EventManager(engine)

    # Add trigger
    manager.add_trigger(
        trigger_id="trigger1",
        name="Test",
        trigger_type=TriggerType.CUSTOM,
        workflow_id="test"
    )

    # Start processing
    await manager.start()

    # Emit event
    await manager.emit_event("custom", {"data": "test"})

    # Give it time to process
    await asyncio.sleep(0.5)

    # Stop
    await manager.stop()

    # Check history
    history = manager.get_event_history()
    assert len(history) > 0


# Task Queue Tests

def test_task_creation():
    """Test creating tasks."""
    task = Task(
        task_id="task1",
        workflow_id="test",
        priority=5,
        max_retries=3
    )

    assert task.task_id == "task1"
    assert task.priority == 5
    assert task.status == TaskStatus.PENDING


def test_task_serialization():
    """Test task serialization."""
    task = Task(
        task_id="task1",
        workflow_id="test",
        context={"key": "value"}
    )

    data = task.to_dict()
    assert data["task_id"] == "task1"

    task2 = Task.from_dict(data)
    assert task2.task_id == task.task_id
    assert task2.context == task.context


@pytest.mark.asyncio
async def test_task_queue():
    """Test task queue."""
    engine = WorkflowEngine()

    # Create workflow
    workflow = WorkflowDefinition(
        workflow_id="test",
        name="Test",
        description="Test",
        steps=[WorkflowStep("step1", "Wait", StepType.WAIT, config={"duration": 0.1})]
    )
    engine.load_workflow(workflow)

    queue = TaskQueue(engine, max_workers=2)

    # Enqueue task
    task_id = await queue.enqueue("test", priority=5)
    assert task_id is not None

    # Start processing
    await queue.start()

    # Wait for task to complete
    await asyncio.sleep(0.5)

    # Check task status
    task = queue.get_task(task_id)
    assert task is not None

    # Stop queue
    await queue.stop()

    # Get stats
    stats = queue.get_stats()
    assert stats["total_tasks"] >= 1


# Progress Tracker Tests

def test_progress_tracker_start():
    """Test starting workflow progress tracking."""
    tracker = ProgressTracker()

    progress = tracker.start_workflow(
        execution_id="exec1",
        workflow_id="test",
        workflow_name="Test Workflow",
        step_ids=["step1", "step2"],
        step_names={"step1": "Step 1", "step2": "Step 2"}
    )

    assert progress.execution_id == "exec1"
    assert len(progress.steps) == 2
    assert progress.status == ProgressStatus.IN_PROGRESS


def test_progress_tracker_update():
    """Test updating step progress."""
    tracker = ProgressTracker()

    progress = tracker.start_workflow(
        execution_id="exec1",
        workflow_id="test",
        workflow_name="Test",
        step_ids=["step1"],
        step_names={"step1": "Step 1"}
    )

    # Update step
    tracker.update_step(
        execution_id="exec1",
        step_id="step1",
        status=ProgressStatus.IN_PROGRESS,
        progress_percent=50.0
    )

    step = progress.steps["step1"]
    assert step.status == ProgressStatus.IN_PROGRESS
    assert step.progress_percent == 50.0


def test_progress_tracker_completion():
    """Test completing workflow."""
    tracker = ProgressTracker()

    progress = tracker.start_workflow(
        execution_id="exec1",
        workflow_id="test",
        workflow_name="Test",
        step_ids=["step1"],
        step_names={"step1": "Step 1"}
    )

    tracker.complete_workflow("exec1", ProgressStatus.COMPLETED)

    assert progress.status == ProgressStatus.COMPLETED
    assert progress.completed_at is not None


@pytest.mark.asyncio
async def test_progress_tracker_notifications():
    """Test progress notifications."""
    tracker = ProgressTracker()

    notifications = []

    async def listener(notification):
        notifications.append(notification)

    tracker.add_listener(listener)

    # Start notifier
    await tracker.start_notifier()

    # Start workflow
    tracker.start_workflow(
        execution_id="exec1",
        workflow_id="test",
        workflow_name="Test",
        step_ids=["step1"],
        step_names={"step1": "Step 1"}
    )

    # Give time for notification
    await asyncio.sleep(0.2)

    # Stop notifier
    await tracker.stop_notifier()

    # Check notifications
    assert len(notifications) > 0


def test_progress_stats():
    """Test progress statistics."""
    tracker = ProgressTracker()

    tracker.start_workflow("exec1", "test1", "Test 1", ["step1"], {"step1": "Step 1"})
    tracker.start_workflow("exec2", "test2", "Test 2", ["step1"], {"step1": "Step 1"})
    tracker.complete_workflow("exec1", ProgressStatus.COMPLETED)

    stats = tracker.get_stats()
    assert stats["total_workflows"] == 2
    assert stats["by_status"]["completed"] == 1
    assert stats["by_status"]["in_progress"] == 1
