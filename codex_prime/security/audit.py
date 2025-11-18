"""Audit logging for security and compliance."""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
import json
import threading


class AuditEventType(Enum):
    """Types of audit events."""

    # Authentication events
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGOUT = "auth.logout"
    TOKEN_CREATED = "auth.token.created"
    TOKEN_REVOKED = "auth.token.revoked"

    # Authorization events
    ACCESS_GRANTED = "authz.access.granted"
    ACCESS_DENIED = "authz.access.denied"
    PERMISSION_CHANGED = "authz.permission.changed"
    ROLE_ASSIGNED = "authz.role.assigned"
    ROLE_REVOKED = "authz.role.revoked"

    # Data events
    DATA_READ = "data.read"
    DATA_CREATED = "data.created"
    DATA_UPDATED = "data.updated"
    DATA_DELETED = "data.deleted"

    # Agent events
    AGENT_CREATED = "agent.created"
    AGENT_EXECUTED = "agent.executed"
    AGENT_DELETED = "agent.deleted"

    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"

    # Security events
    ENCRYPTION_PERFORMED = "security.encryption"
    DECRYPTION_PERFORMED = "security.decryption"
    KEY_ROTATED = "security.key_rotated"
    SECURITY_VIOLATION = "security.violation"

    # System events
    CONFIG_CHANGED = "system.config.changed"
    SYSTEM_ERROR = "system.error"


class AuditSeverity(Enum):
    """Severity levels for audit events."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """Single audit event."""

    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str] = None
    resource_type: Optional[str] = None
    resource_id: Optional[str] = None
    action: Optional[str] = None
    result: str = "success"  # success, failed, denied
    severity: AuditSeverity = AuditSeverity.INFO
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "result": self.result,
            "severity": self.severity.value,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "details": self.details
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AuditEvent':
        """Deserialize from dictionary."""
        return cls(
            event_id=data["event_id"],
            event_type=AuditEventType(data["event_type"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            user_id=data.get("user_id"),
            resource_type=data.get("resource_type"),
            resource_id=data.get("resource_id"),
            action=data.get("action"),
            result=data.get("result", "success"),
            severity=AuditSeverity(data.get("severity", "info")),
            ip_address=data.get("ip_address"),
            user_agent=data.get("user_agent"),
            details=data.get("details", {})
        )


class AuditLogger:
    """Centralized audit logging system."""

    def __init__(self, log_dir: Path, retention_days: int = 90):
        """
        Initialize audit logger.

        Args:
            log_dir: Directory for audit logs
            retention_days: Number of days to retain logs
        """
        self.log_dir = log_dir
        self.retention_days = retention_days
        self.events: List[AuditEvent] = []
        self._lock = threading.Lock()

        # Create log directory
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Load recent events
        self._load_recent_events()

    def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        action: Optional[str] = None,
        result: str = "success",
        severity: AuditSeverity = AuditSeverity.INFO,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        **details
    ) -> AuditEvent:
        """
        Log an audit event.

        Args:
            event_type: Type of event
            user_id: User ID performing the action
            resource_type: Type of resource affected
            resource_id: ID of resource affected
            action: Action performed
            result: Result of action (success, failed, denied)
            severity: Severity level
            ip_address: IP address of request
            user_agent: User agent string
            **details: Additional event details

        Returns:
            Created audit event
        """
        import uuid

        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            timestamp=datetime.now(),
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            result=result,
            severity=severity,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

        with self._lock:
            self.events.append(event)
            self._write_event(event)

        return event

    def log_access(self, user_id: str, resource_type: str, resource_id: str, granted: bool, **details):
        """Log access control event."""
        return self.log(
            event_type=AuditEventType.ACCESS_GRANTED if granted else AuditEventType.ACCESS_DENIED,
            user_id=user_id,
            resource_type=resource_type,
            resource_id=resource_id,
            result="success" if granted else "denied",
            severity=AuditSeverity.WARNING if not granted else AuditSeverity.INFO,
            **details
        )

    def log_login(self, user_id: str, success: bool, ip_address: Optional[str] = None, **details):
        """Log login attempt."""
        return self.log(
            event_type=AuditEventType.LOGIN_SUCCESS if success else AuditEventType.LOGIN_FAILED,
            user_id=user_id,
            result="success" if success else "failed",
            severity=AuditSeverity.WARNING if not success else AuditSeverity.INFO,
            ip_address=ip_address,
            **details
        )

    def log_data_access(self, user_id: str, resource_id: str, operation: str, **details):
        """Log data access event."""
        event_map = {
            "read": AuditEventType.DATA_READ,
            "create": AuditEventType.DATA_CREATED,
            "update": AuditEventType.DATA_UPDATED,
            "delete": AuditEventType.DATA_DELETED,
        }

        return self.log(
            event_type=event_map.get(operation, AuditEventType.DATA_READ),
            user_id=user_id,
            resource_type="data",
            resource_id=resource_id,
            action=operation,
            **details
        )

    def log_security_violation(self, user_id: Optional[str], violation_type: str, **details):
        """Log security violation."""
        return self.log(
            event_type=AuditEventType.SECURITY_VIOLATION,
            user_id=user_id,
            severity=AuditSeverity.CRITICAL,
            result="violation",
            details={"violation_type": violation_type, **details}
        )

    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        user_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        severity: Optional[AuditSeverity] = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """
        Query audit events.

        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            resource_type: Filter by resource type
            start_time: Filter by start time
            end_time: Filter by end time
            severity: Filter by severity
            limit: Maximum number of events to return

        Returns:
            List of matching audit events
        """
        with self._lock:
            results = list(self.events)

        # Apply filters
        if event_type:
            results = [e for e in results if e.event_type == event_type]

        if user_id:
            results = [e for e in results if e.user_id == user_id]

        if resource_type:
            results = [e for e in results if e.resource_type == resource_type]

        if start_time:
            results = [e for e in results if e.timestamp >= start_time]

        if end_time:
            results = [e for e in results if e.timestamp <= end_time]

        if severity:
            results = [e for e in results if e.severity == severity]

        # Sort by timestamp (newest first) and limit
        results.sort(key=lambda e: e.timestamp, reverse=True)
        return results[:limit]

    def get_user_activity(self, user_id: str, days: int = 7) -> List[AuditEvent]:
        """Get recent activity for a user."""
        start_time = datetime.now() - timedelta(days=days)
        return self.query(user_id=user_id, start_time=start_time)

    def get_security_events(self, days: int = 7) -> List[AuditEvent]:
        """Get recent security events."""
        start_time = datetime.now() - timedelta(days=days)
        results = []

        for severity in [AuditSeverity.WARNING, AuditSeverity.ERROR, AuditSeverity.CRITICAL]:
            results.extend(self.query(severity=severity, start_time=start_time))

        return sorted(results, key=lambda e: e.timestamp, reverse=True)

    def get_failed_access_attempts(self, days: int = 1) -> List[AuditEvent]:
        """Get failed access attempts."""
        start_time = datetime.now() - timedelta(days=days)
        return self.query(event_type=AuditEventType.ACCESS_DENIED, start_time=start_time)

    def cleanup_old_logs(self):
        """Remove logs older than retention period."""
        cutoff = datetime.now() - timedelta(days=self.retention_days)

        with self._lock:
            self.events = [e for e in self.events if e.timestamp >= cutoff]

        # Clean up old log files
        for log_file in self.log_dir.glob("audit-*.json"):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace("audit-", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff:
                    log_file.unlink()
            except (ValueError, OSError):
                pass

    def _write_event(self, event: AuditEvent):
        """Write event to daily log file."""
        # Use daily log files
        log_file = self.log_dir / f"audit-{event.timestamp.strftime('%Y-%m-%d')}.json"

        # Append to file
        with open(log_file, 'a') as f:
            f.write(json.dumps(event.to_dict()) + "\n")

    def _load_recent_events(self):
        """Load recent events from log files."""
        cutoff = datetime.now() - timedelta(days=7)

        for log_file in sorted(self.log_dir.glob("audit-*.json")):
            try:
                # Extract date from filename
                date_str = log_file.stem.replace("audit-", "")
                file_date = datetime.strptime(date_str, "%Y-%m-%d")

                if file_date < cutoff:
                    continue

                # Load events from file
                with open(log_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            event_data = json.loads(line)
                            event = AuditEvent.from_dict(event_data)
                            self.events.append(event)

            except (ValueError, json.JSONDecodeError, OSError):
                pass

        # Sort events by timestamp
        self.events.sort(key=lambda e: e.timestamp)
