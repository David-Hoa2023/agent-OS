"""Workflow definition and execution."""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class StepStatus(Enum):
    """Workflow step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Single step in a workflow."""
    step_id: str
    agent_name: str
    task: str
    depends_on: List[str] = field(default_factory=list)  # Step IDs this depends on
    context: Dict[str, Any] = field(default_factory=dict)
    status: StepStatus = StepStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class Workflow:
    """
    Workflow definition using DAG (Directed Acyclic Graph).

    Steps are executed in dependency order.
    """
    workflow_id: str
    name: str
    steps: List[WorkflowStep] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def add_step(
        self,
        step_id: str,
        agent_name: str,
        task: str,
        depends_on: Optional[List[str]] = None,
        **context
    ) -> WorkflowStep:
        """
        Add a step to the workflow.

        Args:
            step_id: Unique step identifier
            agent_name: Name of agent to execute this step
            task: Task description
            depends_on: List of step IDs this depends on
            **context: Additional context for the step

        Returns:
            The created WorkflowStep
        """
        step = WorkflowStep(
            step_id=step_id,
            agent_name=agent_name,
            task=task,
            depends_on=depends_on or [],
            context=context
        )
        self.steps.append(step)
        return step

    def get_step(self, step_id: str) -> Optional[WorkflowStep]:
        """Get step by ID."""
        for step in self.steps:
            if step.step_id == step_id:
                return step
        return None

    def get_ready_steps(self) -> List[WorkflowStep]:
        """
        Get steps that are ready to execute.

        A step is ready if:
        - Its status is PENDING
        - All dependencies are COMPLETED
        """
        ready = []

        for step in self.steps:
            if step.status != StepStatus.PENDING:
                continue

            # Check dependencies
            all_deps_complete = True
            for dep_id in step.depends_on:
                dep_step = self.get_step(dep_id)
                if not dep_step or dep_step.status != StepStatus.COMPLETED:
                    all_deps_complete = False
                    break

            if all_deps_complete:
                ready.append(step)

        return ready

    def is_complete(self) -> bool:
        """Check if workflow is complete."""
        return all(
            step.status in [StepStatus.COMPLETED, StepStatus.SKIPPED, StepStatus.FAILED]
            for step in self.steps
        )

    def has_failed(self) -> bool:
        """Check if any step has failed."""
        return any(step.status == StepStatus.FAILED for step in self.steps)

    def get_progress(self) -> Dict[str, int]:
        """Get workflow progress statistics."""
        status_counts = {
            'total': len(self.steps),
            'pending': 0,
            'running': 0,
            'completed': 0,
            'failed': 0,
            'skipped': 0
        }

        for step in self.steps:
            status_counts[step.status.value] += 1

        return status_counts

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            'workflow_id': self.workflow_id,
            'name': self.name,
            'steps': [
                {
                    'step_id': s.step_id,
                    'agent_name': s.agent_name,
                    'task': s.task,
                    'depends_on': s.depends_on,
                    'status': s.status.value,
                    'result': s.result,
                    'error': s.error
                }
                for s in self.steps
            ],
            'metadata': self.metadata,
            'progress': self.get_progress()
        }
