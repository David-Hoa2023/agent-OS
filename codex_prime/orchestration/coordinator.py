"""Coordinator for multi-agent collaboration."""

import time
import uuid
from typing import Dict, Any, List, Optional
from .workflow import Workflow, WorkflowStep, StepStatus
from .message_bus import MessageBus, Message


class Coordinator:
    """Coordinate multiple agents to complete complex workflows."""

    def __init__(self, message_bus: Optional[MessageBus] = None):
        """
        Initialize coordinator.

        Args:
            message_bus: Optional message bus (created if not provided)
        """
        self.message_bus = message_bus or MessageBus()
        self.agents: Dict[str, Any] = {}  # agent_name -> agent instance
        self.active_workflows: Dict[str, Workflow] = {}

    def register_agent(self, agent_name: str, agent_instance):
        """
        Register an agent with the coordinator.

        Args:
            agent_name: Unique agent name
            agent_instance: Agent instance (must have process() method)
        """
        self.agents[agent_name] = agent_instance

    def unregister_agent(self, agent_name: str):
        """Unregister an agent."""
        if agent_name in self.agents:
            del self.agents[agent_name]

    def create_workflow(self, workflow_id: str, name: str) -> Workflow:
        """
        Create a new workflow.

        Args:
            workflow_id: Unique workflow identifier
            name: Workflow name

        Returns:
            Created workflow
        """
        workflow = Workflow(workflow_id=workflow_id, name=name)
        self.active_workflows[workflow_id] = workflow
        return workflow

    def execute_workflow(
        self,
        workflow: Workflow,
        max_parallel: int = 3,
        timeout: float = 300.0
    ) -> Dict[str, Any]:
        """
        Execute a workflow.

        Args:
            workflow: Workflow to execute
            max_parallel: Maximum parallel step execution
            timeout: Maximum execution time in seconds

        Returns:
            Execution results
        """
        start_time = time.time()
        correlation_id = str(uuid.uuid4())

        while not workflow.is_complete():
            # Check timeout
            if time.time() - start_time > timeout:
                return {
                    'status': 'timeout',
                    'workflow_id': workflow.workflow_id,
                    'progress': workflow.get_progress(),
                    'error': f'Workflow timeout after {timeout}s'
                }

            # Get ready steps
            ready_steps = workflow.get_ready_steps()

            if not ready_steps:
                if workflow.has_failed():
                    break
                # Wait for running steps to complete
                time.sleep(0.1)
                continue

            # Execute steps (up to max_parallel)
            for step in ready_steps[:max_parallel]:
                self._execute_step(step, correlation_id)

            time.sleep(0.1)  # Small delay between batches

        # Workflow complete
        return {
            'status': 'failed' if workflow.has_failed() else 'completed',
            'workflow_id': workflow.workflow_id,
            'progress': workflow.get_progress(),
            'steps': workflow.to_dict()['steps'],
            'duration': time.time() - start_time
        }

    def _execute_step(self, step: WorkflowStep, correlation_id: str):
        """Execute a single workflow step."""
        step.status = StepStatus.RUNNING

        # Get agent
        agent = self.agents.get(step.agent_name)
        if not agent:
            step.status = StepStatus.FAILED
            step.error = f"Agent '{step.agent_name}' not found"
            return

        # Publish start message
        self.message_bus.publish(Message(
            from_agent="coordinator",
            to_agent=step.agent_name,
            message_type="task",
            content={'task': step.task, 'context': step.context},
            correlation_id=correlation_id
        ))

        try:
            # Execute task
            result = agent.process(step.task, context=step.context)
            step.result = result
            step.status = StepStatus.COMPLETED

            # Publish completion message
            self.message_bus.publish(Message(
                from_agent=step.agent_name,
                to_agent="coordinator",
                message_type="response",
                content={'result': result, 'step_id': step.step_id},
                correlation_id=correlation_id
            ))

        except Exception as e:
            step.status = StepStatus.FAILED
            step.error = str(e)

            # Publish error message
            self.message_bus.publish(Message(
                from_agent=step.agent_name,
                to_agent="coordinator",
                message_type="error",
                content={'error': str(e), 'step_id': step.step_id},
                correlation_id=correlation_id
            ))

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        """Get workflow by ID."""
        return self.active_workflows.get(workflow_id)

    def list_workflows(self) -> List[Dict[str, Any]]:
        """List all workflows."""
        return [
            {
                'workflow_id': wf.workflow_id,
                'name': wf.name,
                'progress': wf.get_progress(),
                'is_complete': wf.is_complete()
            }
            for wf in self.active_workflows.values()
        ]
