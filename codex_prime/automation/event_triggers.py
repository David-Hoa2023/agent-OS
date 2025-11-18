"""Event-driven triggers for workflow automation."""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import asyncio
import re


class TriggerType(Enum):
    """Types of event triggers."""

    FILE_CREATED = "file.created"
    FILE_MODIFIED = "file.modified"
    FILE_DELETED = "file.deleted"
    API_CALL = "api.call"
    WEBHOOK = "webhook"
    MEMORY_ADDED = "memory.added"
    AGENT_COMPLETED = "agent.completed"
    WORKFLOW_COMPLETED = "workflow.completed"
    THRESHOLD_EXCEEDED = "threshold.exceeded"
    CUSTOM = "custom"


@dataclass
class EventTrigger:
    """Event trigger configuration."""

    trigger_id: str
    name: str
    trigger_type: TriggerType
    workflow_id: str
    condition: Optional[Dict[str, Any]] = None
    enabled: bool = True
    context_mapper: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def matches_event(self, event: Dict[str, Any]) -> bool:
        """Check if event matches trigger conditions."""
        if not self.enabled:
            return False

        # Check event type
        event_type = event.get("type")
        if event_type != self.trigger_type.value:
            return False

        # Check additional conditions
        if self.condition:
            return self._evaluate_condition(event, self.condition)

        return True

    def _evaluate_condition(self, event: Dict[str, Any], condition: Dict[str, Any]) -> bool:
        """Evaluate condition against event."""
        for key, expected in condition.items():
            actual = event.get(key)

            if isinstance(expected, dict):
                # Operator-based condition
                if "$eq" in expected:
                    if actual != expected["$eq"]:
                        return False
                if "$ne" in expected:
                    if actual == expected["$ne"]:
                        return False
                if "$gt" in expected:
                    if not (actual is not None and actual > expected["$gt"]):
                        return False
                if "$lt" in expected:
                    if not (actual is not None and actual < expected["$lt"]):
                        return False
                if "$regex" in expected:
                    if not (actual and re.match(expected["$regex"], str(actual))):
                        return False
                if "$in" in expected:
                    if actual not in expected["$in"]:
                        return False
            else:
                # Direct equality
                if actual != expected:
                    return False

        return True

    def extract_context(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract context from event for workflow execution."""
        if self.context_mapper:
            return self.context_mapper(event)

        # Default: pass event data as context
        return event.get("data", {})


class EventManager:
    """Manage event-driven workflow triggers."""

    def __init__(self, workflow_engine):
        """
        Initialize event manager.

        Args:
            workflow_engine: WorkflowEngine instance
        """
        self.workflow_engine = workflow_engine
        self.triggers: Dict[str, EventTrigger] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self._running = False
        self._processor_task = None
        self.event_history: List[Dict[str, Any]] = []
        self.max_history = 1000

    def add_trigger(
        self,
        trigger_id: str,
        name: str,
        trigger_type: TriggerType,
        workflow_id: str,
        condition: Optional[Dict[str, Any]] = None,
        context_mapper: Optional[Callable] = None
    ) -> EventTrigger:
        """
        Add an event trigger.

        Args:
            trigger_id: Unique trigger identifier
            name: Human-readable name
            trigger_type: Type of event to trigger on
            workflow_id: Workflow to execute
            condition: Optional condition to filter events
            context_mapper: Optional function to map event to context

        Returns:
            Created event trigger
        """
        trigger = EventTrigger(
            trigger_id=trigger_id,
            name=name,
            trigger_type=trigger_type,
            workflow_id=workflow_id,
            condition=condition,
            context_mapper=context_mapper
        )

        self.triggers[trigger_id] = trigger
        return trigger

    def remove_trigger(self, trigger_id: str):
        """Remove an event trigger."""
        if trigger_id in self.triggers:
            del self.triggers[trigger_id]

    def enable_trigger(self, trigger_id: str):
        """Enable a trigger."""
        if trigger_id in self.triggers:
            self.triggers[trigger_id].enabled = True

    def disable_trigger(self, trigger_id: str):
        """Disable a trigger."""
        if trigger_id in self.triggers:
            self.triggers[trigger_id].enabled = False

    def get_trigger(self, trigger_id: str) -> Optional[EventTrigger]:
        """Get a trigger by ID."""
        return self.triggers.get(trigger_id)

    def list_triggers(self, trigger_type: Optional[TriggerType] = None) -> List[EventTrigger]:
        """List all triggers, optionally filtered by type."""
        triggers = list(self.triggers.values())

        if trigger_type:
            triggers = [t for t in triggers if t.trigger_type == trigger_type]

        return triggers

    async def emit_event(self, event_type: str, data: Optional[Dict[str, Any]] = None):
        """
        Emit an event.

        Args:
            event_type: Type of event
            data: Optional event data
        """
        event = {
            "type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        # Add to queue
        await self.event_queue.put(event)

        # Add to history
        self.event_history.append(event)
        if len(self.event_history) > self.max_history:
            self.event_history.pop(0)

    async def start(self):
        """Start processing events."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())

    async def stop(self):
        """Stop processing events."""
        self._running = False
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass

    async def _process_events(self):
        """Process events from queue."""
        while self._running:
            try:
                # Get event from queue (with timeout)
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=1.0)
                except asyncio.TimeoutError:
                    continue

                # Find matching triggers
                matching_triggers = [
                    trigger for trigger in self.triggers.values()
                    if trigger.matches_event(event)
                ]

                # Execute workflows for matching triggers
                for trigger in matching_triggers:
                    try:
                        context = trigger.extract_context(event)
                        await self.workflow_engine.execute_workflow(
                            workflow_id=trigger.workflow_id,
                            context=context
                        )
                    except Exception as e:
                        import logging
                        logging.error(f"Error executing trigger {trigger.trigger_id}: {e}")

            except asyncio.CancelledError:
                break
            except Exception as e:
                import logging
                logging.error(f"Event processing error: {e}")

    def get_event_history(
        self,
        event_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get event history.

        Args:
            event_type: Optional event type filter
            limit: Maximum number of events to return

        Returns:
            List of events
        """
        events = self.event_history

        if event_type:
            events = [e for e in events if e["type"] == event_type]

        return events[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get event statistics."""
        event_types = {}
        for event in self.event_history:
            event_type = event["type"]
            event_types[event_type] = event_types.get(event_type, 0) + 1

        return {
            "total_events": len(self.event_history),
            "by_type": event_types,
            "total_triggers": len(self.triggers),
            "enabled_triggers": len([t for t in self.triggers.values() if t.enabled])
        }
