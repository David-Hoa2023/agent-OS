"""API key management and authentication."""

from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
import json
import secrets
import hashlib


@dataclass
class APIKey:
    """API key with metadata."""

    key_id: str
    key_hash: str
    name: str
    user_id: str
    scopes: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    last_used: Optional[datetime] = None
    is_active: bool = True
    rate_limit: Optional[int] = None  # requests per minute
    metadata: Dict[str, any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if key is valid (active and not expired)."""
        if not self.is_active:
            return False

        if self.expires_at and datetime.now() > self.expires_at:
            return False

        return True

    def has_scope(self, scope: str) -> bool:
        """Check if key has a specific scope."""
        return scope in self.scopes

    def to_dict(self) -> Dict:
        """Serialize to dictionary."""
        return {
            "key_id": self.key_id,
            "key_hash": self.key_hash,
            "name": self.name,
            "user_id": self.user_id,
            "scopes": list(self.scopes),
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "is_active": self.is_active,
            "rate_limit": self.rate_limit,
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'APIKey':
        """Deserialize from dictionary."""
        return cls(
            key_id=data["key_id"],
            key_hash=data["key_hash"],
            name=data["name"],
            user_id=data["user_id"],
            scopes=set(data.get("scopes", [])),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            last_used=datetime.fromisoformat(data["last_used"]) if data.get("last_used") else None,
            is_active=data.get("is_active", True),
            rate_limit=data.get("rate_limit"),
            metadata=data.get("metadata", {})
        )


class APIKeyManager:
    """Manage API keys for authentication."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize API key manager.

        Args:
            storage_path: Path to store API keys
        """
        self.storage_path = storage_path
        self.keys: Dict[str, APIKey] = {}  # key_id -> APIKey
        self.key_hash_index: Dict[str, str] = {}  # key_hash -> key_id

        # Load existing keys
        if self.storage_path:
            self._load()

    @staticmethod
    def generate_key() -> str:
        """
        Generate a new API key.

        Returns:
            API key string (format: cpx_<random>)
        """
        # Generate cryptographically secure random key
        random_part = secrets.token_urlsafe(32)
        return f"cpx_{random_part}"

    @staticmethod
    def hash_key(api_key: str) -> str:
        """Hash an API key for secure storage."""
        return hashlib.sha256(api_key.encode()).hexdigest()

    def create_key(
        self,
        name: str,
        user_id: str,
        scopes: Optional[Set[str]] = None,
        expires_in_days: Optional[int] = None,
        rate_limit: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> tuple[str, APIKey]:
        """
        Create a new API key.

        Args:
            name: Human-readable name for the key
            user_id: User ID owning the key
            scopes: Set of scopes for the key
            expires_in_days: Number of days until key expires
            rate_limit: Rate limit in requests per minute
            metadata: Additional metadata

        Returns:
            Tuple of (api_key, APIKey object)
        """
        # Generate key
        api_key = self.generate_key()
        key_hash = self.hash_key(api_key)

        # Generate key ID
        import uuid
        key_id = str(uuid.uuid4())

        # Calculate expiration
        expires_at = None
        if expires_in_days:
            expires_at = datetime.now() + timedelta(days=expires_in_days)

        # Create APIKey object
        api_key_obj = APIKey(
            key_id=key_id,
            key_hash=key_hash,
            name=name,
            user_id=user_id,
            scopes=scopes or set(),
            expires_at=expires_at,
            rate_limit=rate_limit,
            metadata=metadata or {}
        )

        # Store
        self.keys[key_id] = api_key_obj
        self.key_hash_index[key_hash] = key_id
        self._save()

        return api_key, api_key_obj

    def validate_key(self, api_key: str) -> Optional[APIKey]:
        """
        Validate an API key.

        Args:
            api_key: API key string

        Returns:
            APIKey object if valid, None otherwise
        """
        key_hash = self.hash_key(api_key)
        key_id = self.key_hash_index.get(key_hash)

        if not key_id:
            return None

        api_key_obj = self.keys.get(key_id)
        if not api_key_obj or not api_key_obj.is_valid():
            return None

        # Update last used timestamp
        api_key_obj.last_used = datetime.now()
        self._save()

        return api_key_obj

    def revoke_key(self, key_id: str):
        """Revoke an API key."""
        if key_id in self.keys:
            self.keys[key_id].is_active = False
            self._save()

    def delete_key(self, key_id: str):
        """Delete an API key."""
        if key_id in self.keys:
            api_key_obj = self.keys[key_id]
            del self.key_hash_index[api_key_obj.key_hash]
            del self.keys[key_id]
            self._save()

    def get_key(self, key_id: str) -> Optional[APIKey]:
        """Get an API key by ID."""
        return self.keys.get(key_id)

    def list_keys(self, user_id: Optional[str] = None, active_only: bool = False) -> List[APIKey]:
        """
        List API keys.

        Args:
            user_id: Filter by user ID
            active_only: Only return active keys

        Returns:
            List of API keys
        """
        keys = list(self.keys.values())

        if user_id:
            keys = [k for k in keys if k.user_id == user_id]

        if active_only:
            keys = [k for k in keys if k.is_valid()]

        return keys

    def cleanup_expired_keys(self):
        """Remove expired keys."""
        expired_keys = [
            key_id for key_id, api_key in self.keys.items()
            if api_key.expires_at and datetime.now() > api_key.expires_at
        ]

        for key_id in expired_keys:
            self.delete_key(key_id)

    def rotate_key(self, key_id: str) -> tuple[str, APIKey]:
        """
        Rotate an API key (create new key with same properties, revoke old).

        Args:
            key_id: ID of key to rotate

        Returns:
            Tuple of (new_api_key, new APIKey object)
        """
        old_key = self.get_key(key_id)
        if not old_key:
            raise ValueError(f"Key {key_id} not found")

        # Create new key with same properties
        new_api_key, new_key_obj = self.create_key(
            name=f"{old_key.name} (rotated)",
            user_id=old_key.user_id,
            scopes=old_key.scopes.copy(),
            expires_in_days=(old_key.expires_at - datetime.now()).days if old_key.expires_at else None,
            rate_limit=old_key.rate_limit,
            metadata=old_key.metadata.copy()
        )

        # Revoke old key
        self.revoke_key(key_id)

        return new_api_key, new_key_obj

    def add_scope(self, key_id: str, scope: str):
        """Add a scope to an API key."""
        if key_id in self.keys:
            self.keys[key_id].scopes.add(scope)
            self._save()

    def remove_scope(self, key_id: str, scope: str):
        """Remove a scope from an API key."""
        if key_id in self.keys:
            self.keys[key_id].scopes.discard(scope)
            self._save()

    def _save(self):
        """Save API keys to storage."""
        if not self.storage_path:
            return

        data = {
            "keys": {key_id: api_key.to_dict() for key_id, api_key in self.keys.items()},
            "key_hash_index": self.key_hash_index
        }

        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load API keys from storage."""
        if not self.storage_path or not self.storage_path.exists():
            return

        with open(self.storage_path, 'r') as f:
            data = json.load(f)

        self.keys = {
            key_id: APIKey.from_dict(key_data)
            for key_id, key_data in data.get("keys", {}).items()
        }

        self.key_hash_index = data.get("key_hash_index", {})
