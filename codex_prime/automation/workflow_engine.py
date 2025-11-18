"""Workflow engine for defining and executing automated workflows."""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import yaml
import json
from datetime import datetime


class StepType(Enum):
    """Types of workflow steps."""

    AGENT = "agent"  # Execute an agent
    TOOL = "tool"  # Execute a tool
    HTTP = "http"  # Make HTTP request
    SCRIPT = "script"  # Run Python script
    CONDITION = "condition"  # Conditional branching
    LOOP = "loop"  # Loop over items
    WAIT = "wait"  # Wait for duration
    PARALLEL = "parallel"  # Execute steps in parallel


@dataclass
class WorkflowStep:
    """Single step in a workflow."""

    step_id: str
    name: str
    type: StepType
    config: Dict[str, Any] = field(default_factory=dict)
    depends_on: List[str] = field(default_factory=list)
    retry_count: int = 0
    retry_delay: int = 5  # seconds
    timeout: Optional[int] = None
    on_error: str = "fail"  # fail, continue, retry

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowStep':
        """Create step from dictionary."""
        return cls(
            step_id=data["step_id"],
            name=data["name"],
            type=StepType(data["type"]),
            config=data.get("config", {}),
            depends_on=data.get("depends_on", []),
            retry_count=data.get("retry_count", 0),
            retry_delay=data.get("retry_delay", 5),
            timeout=data.get("timeout"),
            on_error=data.get("on_error", "fail")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert step to dictionary."""
        return {
            "step_id": self.step_id,
            "name": self.name,
            "type": self.type.value,
            "config": self.config,
            "depends_on": self.depends_on,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "on_error": self.on_error
        }


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""

    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    max_parallel: int = 3
    timeout: Optional[int] = None

    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'WorkflowDefinition':
        """Load workflow from YAML file."""
        with open(yaml_path, 'r') as f:
            data = yaml.safe_load(f)
        return cls.from_dict(data)

    @classmethod
    def from_json(cls, json_path: Path) -> 'WorkflowDefinition':
        """Load workflow from JSON file."""
        with open(json_path, 'r') as f:
            data = json.load(f)
        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Create workflow from dictionary."""
        steps = [WorkflowStep.from_dict(s) for s in data.get("steps", [])]

        return cls(
            workflow_id=data["workflow_id"],
            name=data["name"],
            description=data.get("description", ""),
            steps=steps,
            variables=data.get("variables", {}),
            max_parallel=data.get("max_parallel", 3),
            timeout=data.get("timeout")
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "steps": [s.to_dict() for s in self.steps],
            "variables": self.variables,
            "max_parallel": self.max_parallel,
            "timeout": self.timeout
        }

    def to_yaml(self, yaml_path: Path):
        """Save workflow to YAML file."""
        with open(yaml_path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    def to_json(self, json_path: Path):
        """Save workflow to JSON file."""
        with open(json_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class WorkflowEngine:
    """Engine for executing workflows."""

    def __init__(self):
        """Initialize workflow engine."""
        self.step_handlers: Dict[StepType, Callable] = {}
        self.workflows: Dict[str, WorkflowDefinition] = {}
        self.executions: Dict[str, Dict[str, Any]] = {}

        # Register default handlers
        self._register_default_handlers()

    def _register_default_handlers(self):
        """Register default step type handlers."""
        self.step_handlers[StepType.WAIT] = self._handle_wait
        self.step_handlers[StepType.CONDITION] = self._handle_condition

    def register_handler(self, step_type: StepType, handler: Callable):
        """
        Register a custom step handler.

        Args:
            step_type: Type of step
            handler: Function to handle step execution
        """
        self.step_handlers[step_type] = handler

    def load_workflow(self, workflow: WorkflowDefinition):
        """Load a workflow definition."""
        self.workflows[workflow.workflow_id] = workflow

    def load_workflow_from_file(self, file_path: Path):
        """Load workflow from YAML or JSON file."""
        if file_path.suffix == '.yaml' or file_path.suffix == '.yml':
            workflow = WorkflowDefinition.from_yaml(file_path)
        elif file_path.suffix == '.json':
            workflow = WorkflowDefinition.from_json(file_path)
        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        self.load_workflow(workflow)
        return workflow

    async def execute_workflow(
        self,
        workflow_id: str,
        execution_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow_id: ID of workflow to execute
            execution_id: Optional execution ID (generated if not provided)
            context: Optional context variables

        Returns:
            Execution results
        """
        import uuid
        import asyncio

        if workflow_id not in self.workflows:
            raise ValueError(f"Workflow '{workflow_id}' not found")

        workflow = self.workflows[workflow_id]
        execution_id = execution_id or str(uuid.uuid4())

        # Initialize execution context
        execution = {
            "execution_id": execution_id,
            "workflow_id": workflow_id,
            "status": "running",
            "started_at": datetime.now(),
            "context": {**workflow.variables, **(context or {})},
            "step_results": {},
            "errors": []
        }

        self.executions[execution_id] = execution

        try:
            # Execute steps
            completed_steps = set()

            while len(completed_steps) < len(workflow.steps):
                # Get ready steps
                ready_steps = [
                    step for step in workflow.steps
                    if step.step_id not in completed_steps
                    and all(dep in completed_steps for dep in step.depends_on)
                ]

                if not ready_steps:
                    break

                # Execute steps in parallel (up to max_parallel)
                for i in range(0, len(ready_steps), workflow.max_parallel):
                    batch = ready_steps[i:i + workflow.max_parallel]

                    tasks = [
                        self._execute_step(step, execution)
                        for step in batch
                    ]

                    results = await asyncio.gather(*tasks, return_exceptions=True)

                    # Process results
                    for step, result in zip(batch, results):
                        if isinstance(result, Exception):
                            execution["errors"].append({
                                "step_id": step.step_id,
                                "error": str(result)
                            })

                            if step.on_error == "fail":
                                raise result
                        else:
                            execution["step_results"][step.step_id] = result

                        completed_steps.add(step.step_id)

            execution["status"] = "completed"
            execution["completed_at"] = datetime.now()

        except Exception as e:
            execution["status"] = "failed"
            execution["completed_at"] = datetime.now()
            execution["error"] = str(e)
            raise

        return execution

    async def _execute_step(
        self,
        step: WorkflowStep,
        execution: Dict[str, Any]
    ) -> Any:
        """Execute a single workflow step."""
        import asyncio

        # Get handler
        handler = self.step_handlers.get(step.type)
        if not handler:
            raise ValueError(f"No handler registered for step type: {step.type}")

        # Execute with retry logic
        last_error = None
        for attempt in range(step.retry_count + 1):
            try:
                # Execute with timeout
                if step.timeout:
                    result = await asyncio.wait_for(
                        handler(step, execution),
                        timeout=step.timeout
                    )
                else:
                    result = await handler(step, execution)

                return result

            except Exception as e:
                last_error = e

                if attempt < step.retry_count:
                    await asyncio.sleep(step.retry_delay)
                else:
                    if step.on_error == "continue":
                        return None
                    elif step.on_error == "fail":
                        raise

        if last_error:
            raise last_error

    async def _handle_wait(self, step: WorkflowStep, execution: Dict[str, Any]) -> None:
        """Handle wait step."""
        import asyncio
        duration = step.config.get("duration", 1)
        await asyncio.sleep(duration)

    async def _handle_condition(self, step: WorkflowStep, execution: Dict[str, Any]) -> bool:
        """Handle conditional step."""
        condition = step.config.get("condition")

        # Simple condition evaluation
        if condition:
            # Evaluate condition in context
            context = execution["context"]
            return eval(condition, {"context": context, **context})

        return True

    def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get execution details."""
        return self.executions.get(execution_id)

    def list_executions(self, workflow_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all executions, optionally filtered by workflow."""
        executions = list(self.executions.values())

        if workflow_id:
            executions = [e for e in executions if e["workflow_id"] == workflow_id]

        return executions
