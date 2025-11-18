"""Progress tracking and notifications for workflow execution."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio


class ProgressStatus(Enum):
    """Progress status."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class StepProgress:
    """Progress information for a single step."""

    step_id: str
    step_name: str
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    progress_percent: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error: Optional[str] = None
    output: Any = None
    logs: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "step_id": self.step_id,
            "step_name": self.step_name,
            "status": self.status.value,
            "progress_percent": self.progress_percent,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error": self.error,
            "output": self.output,
            "logs": self.logs
        }


@dataclass
class WorkflowProgress:
    """Progress information for entire workflow."""

    execution_id: str
    workflow_id: str
    workflow_name: str
    status: ProgressStatus = ProgressStatus.NOT_STARTED
    overall_progress: float = 0.0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    steps: Dict[str, StepProgress] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "workflow_name": self.workflow_name,
            "status": self.status.value,
            "overall_progress": self.overall_progress,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "steps": {
                step_id: step.to_dict()
                for step_id, step in self.steps.items()
            },
            "metadata": self.metadata
        }

    def update_overall_progress(self):
        """Calculate overall progress from step progress."""
        if not self.steps:
            self.overall_progress = 0.0
            return

        total_progress = sum(step.progress_percent for step in self.steps.values())
        self.overall_progress = total_progress / len(self.steps)


class ProgressTracker:
    """Track workflow execution progress and send notifications."""

    def __init__(self):
        """Initialize progress tracker."""
        self.workflows: Dict[str, WorkflowProgress] = {}
        self.listeners: List[Callable] = []
        self.notification_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._notifier_task = None

    def start_workflow(
        self,
        execution_id: str,
        workflow_id: str,
        workflow_name: str,
        step_ids: List[str],
        step_names: Dict[str, str]
    ) -> WorkflowProgress:
        """
        Start tracking a workflow execution.

        Args:
            execution_id: Execution ID
            workflow_id: Workflow ID
            workflow_name: Workflow name
            step_ids: List of step IDs
            step_names: Mapping of step IDs to names

        Returns:
            Workflow progress object
        """
        progress = WorkflowProgress(
            execution_id=execution_id,
            workflow_id=workflow_id,
            workflow_name=workflow_name,
            status=ProgressStatus.IN_PROGRESS,
            started_at=datetime.now()
        )

        # Initialize step progress
        for step_id in step_ids:
            progress.steps[step_id] = StepProgress(
                step_id=step_id,
                step_name=step_names.get(step_id, step_id)
            )

        self.workflows[execution_id] = progress

        # Notify listeners
        asyncio.create_task(self._notify("workflow_started", progress))

        return progress

    def update_step(
        self,
        execution_id: str,
        step_id: str,
        status: Optional[ProgressStatus] = None,
        progress_percent: Optional[float] = None,
        error: Optional[str] = None,
        output: Any = None,
        log: Optional[str] = None
    ):
        """
        Update step progress.

        Args:
            execution_id: Execution ID
            step_id: Step ID
            status: Optional new status
            progress_percent: Optional progress percentage
            error: Optional error message
            output: Optional step output
            log: Optional log message
        """
        workflow = self.workflows.get(execution_id)
        if not workflow:
            return

        step = workflow.steps.get(step_id)
        if not step:
            return

        # Update status
        if status:
            old_status = step.status
            step.status = status

            if status == ProgressStatus.IN_PROGRESS and old_status == ProgressStatus.NOT_STARTED:
                step.started_at = datetime.now()

            elif status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.SKIPPED]:
                step.completed_at = datetime.now()
                if status == ProgressStatus.COMPLETED:
                    step.progress_percent = 100.0

        # Update progress
        if progress_percent is not None:
            step.progress_percent = max(0.0, min(100.0, progress_percent))

        # Update error
        if error:
            step.error = error

        # Update output
        if output is not None:
            step.output = output

        # Add log
        if log:
            step.logs.append(f"[{datetime.now().isoformat()}] {log}")

        # Update overall progress
        workflow.update_overall_progress()

        # Notify listeners
        asyncio.create_task(self._notify("step_updated", {
            "execution_id": execution_id,
            "step_id": step_id,
            "step": step,
            "workflow": workflow
        }))

    def complete_workflow(
        self,
        execution_id: str,
        status: ProgressStatus = ProgressStatus.COMPLETED,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Mark workflow as completed.

        Args:
            execution_id: Execution ID
            status: Final status
            metadata: Optional metadata
        """
        workflow = self.workflows.get(execution_id)
        if not workflow:
            return

        workflow.status = status
        workflow.completed_at = datetime.now()

        if metadata:
            workflow.metadata.update(metadata)

        # Notify listeners
        asyncio.create_task(self._notify("workflow_completed", workflow))

    def get_progress(self, execution_id: str) -> Optional[WorkflowProgress]:
        """Get workflow progress."""
        return self.workflows.get(execution_id)

    def list_active_workflows(self) -> List[WorkflowProgress]:
        """List all active workflow executions."""
        return [
            w for w in self.workflows.values()
            if w.status == ProgressStatus.IN_PROGRESS
        ]

    def add_listener(self, listener: Callable):
        """
        Add a progress listener.

        Args:
            listener: Async function to call on progress updates
        """
        self.listeners.append(listener)

    def remove_listener(self, listener: Callable):
        """Remove a progress listener."""
        if listener in self.listeners:
            self.listeners.remove(listener)

    async def _notify(self, event_type: str, data: Any):
        """Notify all listeners of a progress event."""
        notification = {
            "type": event_type,
            "timestamp": datetime.now(),
            "data": data
        }

        await self.notification_queue.put(notification)

    async def start_notifier(self):
        """Start the notification processor."""
        if self._running:
            return

        self._running = True
        self._notifier_task = asyncio.create_task(self._process_notifications())

    async def stop_notifier(self):
        """Stop the notification processor."""
        self._running = False
        if self._notifier_task:
            self._notifier_task.cancel()
            try:
                await self._notifier_task
            except asyncio.CancelledError:
                pass

    async def _process_notifications(self):
        """Process notifications from queue."""
        while self._running:
            try:
                # Get notification
                try:
                    notification = await asyncio.wait_for(
                        self.notification_queue.get(),
                        timeout=1.0
                    )
                except asyncio.TimeoutError:
                    continue

                # Call all listeners
                for listener in self.listeners:
                    try:
                        await listener(notification)
                    except Exception as e:
                        import logging
                        logging.error(f"Listener error: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging
                logging.error(f"Notification processing error: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get progress tracking statistics."""
        total = len(self.workflows)
        by_status = {}

        for status in ProgressStatus:
            by_status[status.value] = len([
                w for w in self.workflows.values()
                if w.status == status
            ])

        return {
            "total_workflows": total,
            "by_status": by_status,
            "active_listeners": len(self.listeners),
            "pending_notifications": self.notification_queue.qsize()
        }
