"""Cron-based scheduler for periodic workflow execution."""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import asyncio
from pathlib import Path
import json

# Try to import croniter for cron parsing
try:
    from croniter import croniter
    CRONITER_AVAILABLE = True
except ImportError:
    CRONITER_AVAILABLE = False


@dataclass
class Schedule:
    """Schedule configuration."""

    cron_expression: str
    enabled: bool = True
    timezone: str = "UTC"
    max_runs: Optional[int] = None
    run_count: int = 0
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None

    def should_run(self) -> bool:
        """Check if schedule should run now."""
        if not self.enabled:
            return False

        if self.max_runs and self.run_count >= self.max_runs:
            return False

        if not self.next_run:
            return True

        return datetime.now() >= self.next_run

    def calculate_next_run(self):
        """Calculate next run time based on cron expression."""
        if not CRONITER_AVAILABLE:
            # Fallback: simple interval parsing
            return self._parse_simple_interval()

        base_time = self.last_run or datetime.now()
        cron = croniter(self.cron_expression, base_time)
        self.next_run = cron.get_next(datetime)

    def _parse_simple_interval(self) -> datetime:
        """Simple interval parser for common patterns."""
        # Support simple patterns like "*/5 * * * *" (every 5 minutes)
        parts = self.cron_expression.split()

        if len(parts) >= 1:
            minute_part = parts[0]

            if minute_part.startswith("*/"):
                # Every N minutes
                interval = int(minute_part[2:])
                return datetime.now() + timedelta(minutes=interval)
            elif minute_part.isdigit():
                # Specific minute
                target_minute = int(minute_part)
                now = datetime.now()
                target = now.replace(minute=target_minute, second=0, microsecond=0)

                if target <= now:
                    target += timedelta(hours=1)

                return target

        # Default: 1 hour
        return datetime.now() + timedelta(hours=1)


@dataclass
class ScheduledTask:
    """A scheduled task."""

    task_id: str
    name: str
    workflow_id: str
    schedule: Schedule
    context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "workflow_id": self.workflow_id,
            "schedule": {
                "cron_expression": self.schedule.cron_expression,
                "enabled": self.schedule.enabled,
                "timezone": self.schedule.timezone,
                "max_runs": self.schedule.max_runs,
                "run_count": self.schedule.run_count,
                "last_run": self.schedule.last_run.isoformat() if self.schedule.last_run else None,
                "next_run": self.schedule.next_run.isoformat() if self.schedule.next_run else None,
            },
            "context": self.context,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """Deserialize from dictionary."""
        schedule_data = data["schedule"]
        schedule = Schedule(
            cron_expression=schedule_data["cron_expression"],
            enabled=schedule_data.get("enabled", True),
            timezone=schedule_data.get("timezone", "UTC"),
            max_runs=schedule_data.get("max_runs"),
            run_count=schedule_data.get("run_count", 0),
            last_run=datetime.fromisoformat(schedule_data["last_run"]) if schedule_data.get("last_run") else None,
            next_run=datetime.fromisoformat(schedule_data["next_run"]) if schedule_data.get("next_run") else None,
        )

        return cls(
            task_id=data["task_id"],
            name=data["name"],
            workflow_id=data["workflow_id"],
            schedule=schedule,
            context=data.get("context", {}),
            metadata=data.get("metadata", {})
        )


class CronScheduler:
    """Cron-based scheduler for workflow execution."""

    def __init__(self, workflow_engine, storage_path: Optional[Path] = None):
        """
        Initialize cron scheduler.

        Args:
            workflow_engine: WorkflowEngine instance
            storage_path: Optional path to persist schedules
        """
        self.workflow_engine = workflow_engine
        self.storage_path = storage_path
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._scheduler_task = None

        # Load existing tasks
        if self.storage_path and self.storage_path.exists():
            self._load()

    def add_task(
        self,
        task_id: str,
        name: str,
        workflow_id: str,
        cron_expression: str,
        context: Optional[Dict[str, Any]] = None,
        max_runs: Optional[int] = None
    ) -> ScheduledTask:
        """
        Add a scheduled task.

        Args:
            task_id: Unique task identifier
            name: Human-readable name
            workflow_id: Workflow to execute
            cron_expression: Cron schedule expression
            context: Optional context variables
            max_runs: Optional maximum number of runs

        Returns:
            Created scheduled task
        """
        schedule = Schedule(
            cron_expression=cron_expression,
            max_runs=max_runs
        )
        schedule.calculate_next_run()

        task = ScheduledTask(
            task_id=task_id,
            name=name,
            workflow_id=workflow_id,
            schedule=schedule,
            context=context or {}
        )

        self.tasks[task_id] = task
        self._save()

        return task

    def remove_task(self, task_id: str):
        """Remove a scheduled task."""
        if task_id in self.tasks:
            del self.tasks[task_id]
            self._save()

    def enable_task(self, task_id: str):
        """Enable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].schedule.enabled = True
            self._save()

    def disable_task(self, task_id: str):
        """Disable a task."""
        if task_id in self.tasks:
            self.tasks[task_id].schedule.enabled = False
            self._save()

    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(self, enabled_only: bool = False) -> List[ScheduledTask]:
        """List all tasks."""
        tasks = list(self.tasks.values())

        if enabled_only:
            tasks = [t for t in tasks if t.schedule.enabled]

        return tasks

    async def start(self):
        """Start the scheduler."""
        if self._running:
            return

        self._running = True
        self._scheduler_task = asyncio.create_task(self._scheduler_loop())

    async def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._scheduler_task:
            self._scheduler_task.cancel()
            try:
                await self._scheduler_task
            except asyncio.CancelledError:
                pass

    async def _scheduler_loop(self):
        """Main scheduler loop."""
        while self._running:
            try:
                await self._check_and_execute_tasks()
                await asyncio.sleep(30)  # Check every 30 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging
                logging.error(f"Scheduler error: {e}")
                await asyncio.sleep(60)

    async def _check_and_execute_tasks(self):
        """Check and execute due tasks."""
        for task in list(self.tasks.values()):
            if task.schedule.should_run():
                try:
                    await self._execute_task(task)
                except Exception as e:
                    import logging
                    logging.error(f"Error executing task {task.task_id}: {e}")

    async def _execute_task(self, task: ScheduledTask):
        """Execute a scheduled task."""
        import uuid

        # Execute workflow
        execution_id = f"{task.task_id}-{uuid.uuid4().hex[:8]}"

        await self.workflow_engine.execute_workflow(
            workflow_id=task.workflow_id,
            execution_id=execution_id,
            context=task.context
        )

        # Update task schedule
        task.schedule.last_run = datetime.now()
        task.schedule.run_count += 1
        task.schedule.calculate_next_run()

        self._save()

    def _save(self):
        """Save tasks to storage."""
        if not self.storage_path:
            return

        data = {
            "tasks": {
                task_id: task.to_dict()
                for task_id, task in self.tasks.items()
            }
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load tasks from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, 'r') as f:
            data = json.load(f)

        for task_id, task_data in data.get("tasks", {}).items():
            task = ScheduledTask.from_dict(task_data)
            self.tasks[task_id] = task
