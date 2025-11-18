"""Role-Based Access Control (RBAC) system."""

from typing import Set, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
import json
from pathlib import Path


class Permission(Enum):
    """System permissions."""

    # Agent permissions
    AGENT_READ = "agent:read"
    AGENT_WRITE = "agent:write"
    AGENT_EXECUTE = "agent:execute"
    AGENT_DELETE = "agent:delete"

    # Memory permissions
    MEMORY_READ = "memory:read"
    MEMORY_WRITE = "memory:write"
    MEMORY_DELETE = "memory:delete"

    # Tool permissions
    TOOL_EXECUTE = "tool:execute"
    TOOL_MANAGE = "tool:manage"

    # Workflow permissions
    WORKFLOW_READ = "workflow:read"
    WORKFLOW_WRITE = "workflow:write"
    WORKFLOW_EXECUTE = "workflow:execute"

    # Admin permissions
    USER_MANAGE = "user:manage"
    ROLE_MANAGE = "role:manage"
    SYSTEM_CONFIG = "system:config"
    AUDIT_READ = "audit:read"


@dataclass
class Role:
    """User role with permissions."""

    name: str
    description: str
    permissions: Set[Permission] = field(default_factory=set)

    def has_permission(self, permission: Permission) -> bool:
        """Check if role has a specific permission."""
        return permission in self.permissions

    def add_permission(self, permission: Permission):
        """Add a permission to the role."""
        self.permissions.add(permission)

    def remove_permission(self, permission: Permission):
        """Remove a permission from the role."""
        self.permissions.discard(permission)

    def to_dict(self) -> Dict:
        """Serialize role to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "permissions": [p.value for p in self.permissions]
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Role':
        """Deserialize role from dictionary."""
        permissions = {Permission(p) for p in data.get("permissions", [])}
        return cls(
            name=data["name"],
            description=data["description"],
            permissions=permissions
        )


@dataclass
class User:
    """User with roles and permissions."""

    user_id: str
    username: str
    email: str
    roles: Set[Role] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    is_active: bool = True

    def has_permission(self, permission: Permission) -> bool:
        """Check if user has a specific permission through any role."""
        if not self.is_active:
            return False
        return any(role.has_permission(permission) for role in self.roles)

    def has_any_permission(self, permissions: List[Permission]) -> bool:
        """Check if user has any of the specified permissions."""
        return any(self.has_permission(p) for p in permissions)

    def has_all_permissions(self, permissions: List[Permission]) -> bool:
        """Check if user has all of the specified permissions."""
        return all(self.has_permission(p) for p in permissions)

    def add_role(self, role: Role):
        """Add a role to the user."""
        self.roles.add(role)

    def remove_role(self, role: Role):
        """Remove a role from the user."""
        self.roles.discard(role)

    def get_all_permissions(self) -> Set[Permission]:
        """Get all permissions from all roles."""
        permissions = set()
        for role in self.roles:
            permissions.update(role.permissions)
        return permissions

    def to_dict(self) -> Dict:
        """Serialize user to dictionary."""
        return {
            "user_id": self.user_id,
            "username": self.username,
            "email": self.email,
            "roles": [role.name for role in self.roles],
            "created_at": self.created_at.isoformat(),
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "is_active": self.is_active
        }


class RBACManager:
    """Manage roles, users, and permissions."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize RBAC manager.

        Args:
            storage_path: Path to store RBAC data
        """
        self.storage_path = storage_path
        self.roles: Dict[str, Role] = {}
        self.users: Dict[str, User] = {}

        # Create default roles
        self._create_default_roles()

        # Load existing data if storage path provided
        if self.storage_path:
            self._load()

    def _create_default_roles(self):
        """Create default system roles."""
        # Admin role - all permissions
        admin = Role("admin", "System administrator with full access")
        admin.permissions = set(Permission)
        self.roles["admin"] = admin

        # Developer role - agent and workflow management
        developer = Role("developer", "Developer with agent and workflow access")
        developer.permissions = {
            Permission.AGENT_READ,
            Permission.AGENT_WRITE,
            Permission.AGENT_EXECUTE,
            Permission.MEMORY_READ,
            Permission.MEMORY_WRITE,
            Permission.TOOL_EXECUTE,
            Permission.WORKFLOW_READ,
            Permission.WORKFLOW_WRITE,
            Permission.WORKFLOW_EXECUTE,
        }
        self.roles["developer"] = developer

        # Operator role - execute only
        operator = Role("operator", "Operator with execution permissions")
        operator.permissions = {
            Permission.AGENT_READ,
            Permission.AGENT_EXECUTE,
            Permission.MEMORY_READ,
            Permission.TOOL_EXECUTE,
            Permission.WORKFLOW_READ,
            Permission.WORKFLOW_EXECUTE,
        }
        self.roles["operator"] = operator

        # Viewer role - read only
        viewer = Role("viewer", "Read-only access")
        viewer.permissions = {
            Permission.AGENT_READ,
            Permission.MEMORY_READ,
            Permission.WORKFLOW_READ,
            Permission.AUDIT_READ,
        }
        self.roles["viewer"] = viewer

    def create_role(self, name: str, description: str, permissions: Optional[Set[Permission]] = None) -> Role:
        """Create a new role."""
        if name in self.roles:
            raise ValueError(f"Role '{name}' already exists")

        role = Role(name, description, permissions or set())
        self.roles[name] = role
        self._save()
        return role

    def get_role(self, name: str) -> Optional[Role]:
        """Get a role by name."""
        return self.roles.get(name)

    def delete_role(self, name: str):
        """Delete a role."""
        if name in ["admin", "developer", "operator", "viewer"]:
            raise ValueError("Cannot delete default roles")

        if name in self.roles:
            del self.roles[name]
            self._save()

    def create_user(self, user_id: str, username: str, email: str, roles: Optional[List[str]] = None) -> User:
        """Create a new user."""
        if user_id in self.users:
            raise ValueError(f"User '{user_id}' already exists")

        user = User(user_id=user_id, username=username, email=email)

        # Add roles
        if roles:
            for role_name in roles:
                role = self.get_role(role_name)
                if role:
                    user.add_role(role)

        self.users[user_id] = user
        self._save()
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        return self.users.get(user_id)

    def delete_user(self, user_id: str):
        """Delete a user."""
        if user_id in self.users:
            del self.users[user_id]
            self._save()

    def grant_role(self, user_id: str, role_name: str):
        """Grant a role to a user."""
        user = self.get_user(user_id)
        role = self.get_role(role_name)

        if not user:
            raise ValueError(f"User '{user_id}' not found")
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        user.add_role(role)
        self._save()

    def revoke_role(self, user_id: str, role_name: str):
        """Revoke a role from a user."""
        user = self.get_user(user_id)
        role = self.get_role(role_name)

        if not user:
            raise ValueError(f"User '{user_id}' not found")
        if not role:
            raise ValueError(f"Role '{role_name}' not found")

        user.remove_role(role)
        self._save()

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if a user has a specific permission."""
        user = self.get_user(user_id)
        if not user:
            return False
        return user.has_permission(permission)

    def require_permission(self, user_id: str, permission: Permission):
        """Require a user to have a permission, raise exception if not."""
        if not self.check_permission(user_id, permission):
            raise PermissionError(f"User '{user_id}' does not have permission '{permission.value}'")

    def list_users(self) -> List[User]:
        """List all users."""
        return list(self.users.values())

    def list_roles(self) -> List[Role]:
        """List all roles."""
        return list(self.roles.values())

    def _save(self):
        """Save RBAC data to storage."""
        if not self.storage_path:
            return

        data = {
            "roles": {name: role.to_dict() for name, role in self.roles.items()},
            "users": {
                user_id: {
                    **user.to_dict(),
                    "roles": [role.name for role in user.roles]
                }
                for user_id, user in self.users.items()
            }
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load RBAC data from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, 'r') as f:
            data = json.load(f)

        # Load roles
        for role_data in data.get("roles", {}).values():
            role = Role.from_dict(role_data)
            self.roles[role.name] = role

        # Load users
        for user_id, user_data in data.get("users", {}).items():
            user = User(
                user_id=user_id,
                username=user_data["username"],
                email=user_data["email"],
                created_at=datetime.fromisoformat(user_data["created_at"]),
                last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                is_active=user_data.get("is_active", True)
            )

            # Add roles
            for role_name in user_data.get("roles", []):
                role = self.get_role(role_name)
                if role:
                    user.add_role(role)

            self.users[user_id] = user
