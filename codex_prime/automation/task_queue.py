"""Background task queue for asynchronous workflow execution."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import asyncio
import json
import uuid


class TaskStatus(Enum):
    """Task execution status."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRY = "retry"


@dataclass
class TaskResult:
    """Result of a task execution."""

    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    attempts: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "attempts": self.attempts
        }


@dataclass
class Task:
    """Background task."""

    task_id: str
    workflow_id: str
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0  # Higher priority = executed first
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    timeout: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    result: Optional[TaskResult] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "task_id": self.task_id,
            "workflow_id": self.workflow_id,
            "context": self.context,
            "priority": self.priority,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "created_at": self.created_at.isoformat(),
            "scheduled_at": self.scheduled_at.isoformat() if self.scheduled_at else None,
            "status": self.status.value,
            "result": self.result.to_dict() if self.result else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Deserialize from dictionary."""
        task = cls(
            task_id=data["task_id"],
            workflow_id=data["workflow_id"],
            context=data.get("context", {}),
            priority=data.get("priority", 0),
            max_retries=data.get("max_retries", 3),
            retry_delay=data.get("retry_delay", 60),
            timeout=data.get("timeout"),
            created_at=datetime.fromisoformat(data["created_at"]),
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if data.get("scheduled_at") else None,
            status=TaskStatus(data.get("status", "pending"))
        )

        if data.get("result"):
            result_data = data["result"]
            task.result = TaskResult(
                task_id=result_data["task_id"],
                status=TaskStatus(result_data["status"]),
                result=result_data.get("result"),
                error=result_data.get("error"),
                started_at=datetime.fromisoformat(result_data["started_at"]) if result_data.get("started_at") else None,
                completed_at=datetime.fromisoformat(result_data["completed_at"]) if result_data.get("completed_at") else None,
                attempts=result_data.get("attempts", 0)
            )

        return task


class TaskQueue:
    """Async task queue for background workflow execution."""

    def __init__(
        self,
        workflow_engine,
        max_workers: int = 5,
        storage_path: Optional[Path] = None
    ):
        """
        Initialize task queue.

        Args:
            workflow_engine: WorkflowEngine instance
            max_workers: Maximum concurrent workers
            storage_path: Optional path to persist tasks
        """
        self.workflow_engine = workflow_engine
        self.max_workers = max_workers
        self.storage_path = storage_path

        self.tasks: Dict[str, Task] = {}
        self.pending_queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self.workers: List[asyncio.Task] = []
        self._running = False

        # Callbacks
        self.on_task_complete: Optional[Callable] = None
        self.on_task_failed: Optional[Callable] = None

        # Load existing tasks
        if self.storage_path and self.storage_path.exists():
            self._load()

    async def enqueue(
        self,
        workflow_id: str,
        context: Optional[Dict[str, Any]] = None,
        priority: int = 0,
        scheduled_at: Optional[datetime] = None,
        max_retries: int = 3
    ) -> str:
        """
        Enqueue a task for background execution.

        Args:
            workflow_id: Workflow to execute
            context: Optional context variables
            priority: Task priority (higher = executed first)
            scheduled_at: Optional scheduled execution time
            max_retries: Maximum retry attempts

        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id,
            workflow_id=workflow_id,
            context=context or {},
            priority=priority,
            max_retries=max_retries,
            scheduled_at=scheduled_at
        )

        self.tasks[task_id] = task

        # Add to pending queue (negative priority for max-heap)
        await self.pending_queue.put((-priority, task_id))

        self._save()

        return task_id

    async def start(self):
        """Start processing tasks."""
        if self._running:
            return

        self._running = True

        # Start worker tasks
        self.workers = [
            asyncio.create_task(self._worker(i))
            for i in range(self.max_workers)
        ]

    async def stop(self):
        """Stop processing tasks."""
        self._running = False

        # Cancel all workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        self.workers.clear()

    async def _worker(self, worker_id: int):
        """Worker task that processes queue."""
        while self._running:
            try:
                # Get task from queue (with timeout)
                try:
                    _, task_id = await asyncio.wait_for(
                        self.pending_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                task = self.tasks.get(task_id)
                if not task:
                    continue

                # Check if task should be executed now
                if task.scheduled_at and datetime.now() < task.scheduled_at:
                    # Re-queue for later
                    await self.pending_queue.put((-task.priority, task_id))
                    await asyncio.sleep(1)
                    continue

                # Execute task
                await self._execute_task(task)

            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging
                logging.error(f"Worker {worker_id} error: {e}")

    async def _execute_task(self, task: Task):
        """Execute a single task."""
        task.status = TaskStatus.RUNNING

        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING,
            started_at=datetime.now()
        )

        task.result = result

        try:
            # Execute workflow with timeout
            if task.timeout:
                execution = await asyncio.wait_for(
                    self.workflow_engine.execute_workflow(
                        workflow_id=task.workflow_id,
                        execution_id=task.task_id,
                        context=task.context
                    ),
                    timeout=task.timeout
                )
            else:
                execution = await self.workflow_engine.execute_workflow(
                    workflow_id=task.workflow_id,
                    execution_id=task.task_id,
                    context=task.context
                )

            # Success
            result.status = TaskStatus.COMPLETED
            result.result = execution
            result.completed_at = datetime.now()

            task.status = TaskStatus.COMPLETED

            # Call completion callback
            if self.on_task_complete:
                await self.on_task_complete(task)

        except Exception as e:
            # Failure
            result.attempts += 1
            result.error = str(e)
            result.completed_at = datetime.now()

            # Retry logic
            if result.attempts < task.max_retries:
                result.status = TaskStatus.RETRY
                task.status = TaskStatus.PENDING

                # Re-queue with delay
                await asyncio.sleep(task.retry_delay)
                await self.pending_queue.put((-task.priority, task.task_id))

            else:
                result.status = TaskStatus.FAILED
                task.status = TaskStatus.FAILED

                # Call failure callback
                if self.on_task_failed:
                    await self.on_task_failed(task)

        self._save()

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task by ID."""
        return self.tasks.get(task_id)

    def list_tasks(
        self,
        status: Optional[TaskStatus] = None,
        limit: int = 100
    ) -> List[Task]:
        """List tasks, optionally filtered by status."""
        tasks = list(self.tasks.values())

        if status:
            tasks = [t for t in tasks if t.status == status]

        # Sort by created_at (newest first)
        tasks.sort(key=lambda t: t.created_at, reverse=True)

        return tasks[:limit]

    def get_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        statuses = {}
        for status in TaskStatus:
            statuses[status.value] = len([
                t for t in self.tasks.values()
                if t.status == status
            ])

        return {
            "total_tasks": len(self.tasks),
            "by_status": statuses,
            "pending_queue_size": self.pending_queue.qsize(),
            "workers": len(self.workers),
            "running": self._running
        }

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        task = self.get_task(task_id)
        if not task:
            return False

        if task.status == TaskStatus.PENDING:
            task.status = TaskStatus.CANCELLED
            self._save()
            return True

        return False

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
            task = Task.from_dict(task_data)
            self.tasks[task_id] = task

            # Re-queue pending tasks
            if task.status == TaskStatus.PENDING:
                asyncio.create_task(
                    self.pending_queue.put((-task.priority, task_id))
                )
