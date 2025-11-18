"""Encryption utilities for sensitive data."""

from typing import Dict, Any, Optional
from pathlib import Path
import json
import base64
import hashlib
import secrets
from dataclasses import dataclass, field
from datetime import datetime

# Try to import cryptography
try:
    from cryptography.fernet import Fernet
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


@dataclass
class EncryptedData:
    """Encrypted data container."""

    ciphertext: str
    salt: str
    encrypted_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "ciphertext": self.ciphertext,
            "salt": self.salt,
            "encrypted_at": self.encrypted_at.isoformat(),
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EncryptedData':
        """Deserialize from dictionary."""
        return cls(
            ciphertext=data["ciphertext"],
            salt=data["salt"],
            encrypted_at=datetime.fromisoformat(data["encrypted_at"]),
            metadata=data.get("metadata", {})
        )


class EncryptionManager:
    """Manage encryption and decryption of sensitive data."""

    def __init__(self, master_key: Optional[str] = None):
        """
        Initialize encryption manager.

        Args:
            master_key: Master encryption key (will be generated if not provided)
        """
        if not CRYPTO_AVAILABLE:
            raise ImportError("cryptography package required for encryption. Install with: pip install cryptography")

        self.master_key = master_key or self._generate_master_key()

    @staticmethod
    def _generate_master_key() -> str:
        """Generate a new master key."""
        return Fernet.generate_key().decode('utf-8')

    def _derive_key(self, password: str, salt: bytes) -> bytes:
        """Derive encryption key from password using PBKDF2."""
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        return base64.urlsafe_b64encode(kdf.derive(password.encode()))

    def encrypt(self, data: str, password: Optional[str] = None) -> EncryptedData:
        """
        Encrypt data.

        Args:
            data: Data to encrypt
            password: Optional password (uses master key if not provided)

        Returns:
            Encrypted data container
        """
        # Generate salt
        salt = secrets.token_bytes(16)

        # Derive key
        key = self._derive_key(password or self.master_key, salt)

        # Encrypt
        f = Fernet(key)
        ciphertext = f.encrypt(data.encode('utf-8'))

        return EncryptedData(
            ciphertext=base64.b64encode(ciphertext).decode('utf-8'),
            salt=base64.b64encode(salt).decode('utf-8')
        )

    def decrypt(self, encrypted_data: EncryptedData, password: Optional[str] = None) -> str:
        """
        Decrypt data.

        Args:
            encrypted_data: Encrypted data container
            password: Optional password (uses master key if not provided)

        Returns:
            Decrypted data

        Raises:
            ValueError: If decryption fails
        """
        # Decode salt and ciphertext
        salt = base64.b64decode(encrypted_data.salt)
        ciphertext = base64.b64decode(encrypted_data.ciphertext)

        # Derive key
        key = self._derive_key(password or self.master_key, salt)

        # Decrypt
        try:
            f = Fernet(key)
            plaintext = f.decrypt(ciphertext)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {str(e)}")

    def encrypt_dict(self, data: Dict[str, Any], password: Optional[str] = None) -> EncryptedData:
        """Encrypt a dictionary."""
        json_data = json.dumps(data)
        return self.encrypt(json_data, password)

    def decrypt_dict(self, encrypted_data: EncryptedData, password: Optional[str] = None) -> Dict[str, Any]:
        """Decrypt to a dictionary."""
        json_data = self.decrypt(encrypted_data, password)
        return json.loads(json_data)

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        """Verify a password against its hash."""
        return EncryptionManager.hash_password(password) == password_hash


class SecureVault:
    """Secure storage for sensitive data with encryption."""

    def __init__(self, vault_path: Path, encryption_manager: EncryptionManager):
        """
        Initialize secure vault.

        Args:
            vault_path: Path to vault storage
            encryption_manager: Encryption manager instance
        """
        self.vault_path = vault_path
        self.encryption_manager = encryption_manager
        self.data: Dict[str, EncryptedData] = {}

        # Load existing data
        self._load()

    def store(self, key: str, value: str, password: Optional[str] = None, metadata: Optional[Dict] = None):
        """
        Store encrypted data.

        Args:
            key: Storage key
            value: Value to encrypt and store
            password: Optional password (uses master key if not provided)
            metadata: Optional metadata
        """
        encrypted = self.encryption_manager.encrypt(value, password)
        if metadata:
            encrypted.metadata = metadata

        self.data[key] = encrypted
        self._save()

    def retrieve(self, key: str, password: Optional[str] = None) -> Optional[str]:
        """
        Retrieve and decrypt data.

        Args:
            key: Storage key
            password: Optional password (uses master key if not provided)

        Returns:
            Decrypted value or None if not found
        """
        encrypted = self.data.get(key)
        if not encrypted:
            return None

        try:
            return self.encryption_manager.decrypt(encrypted, password)
        except ValueError:
            return None

    def store_dict(self, key: str, value: Dict[str, Any], password: Optional[str] = None, metadata: Optional[Dict] = None):
        """Store encrypted dictionary."""
        encrypted = self.encryption_manager.encrypt_dict(value, password)
        if metadata:
            encrypted.metadata = metadata

        self.data[key] = encrypted
        self._save()

    def retrieve_dict(self, key: str, password: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Retrieve and decrypt dictionary."""
        encrypted = self.data.get(key)
        if not encrypted:
            return None

        try:
            return self.encryption_manager.decrypt_dict(encrypted, password)
        except ValueError:
            return None

    def delete(self, key: str):
        """Delete stored data."""
        if key in self.data:
            del self.data[key]
            self._save()

    def list_keys(self) -> list:
        """List all storage keys."""
        return list(self.data.keys())

    def clear(self):
        """Clear all stored data."""
        self.data.clear()
        self._save()

    def _save(self):
        """Save vault to disk."""
        self.vault_path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            key: encrypted.to_dict()
            for key, encrypted in self.data.items()
        }

        with open(self.vault_path, 'w') as f:
            json.dump(data, f, indent=2)

    def _load(self):
        """Load vault from disk."""
        if not self.vault_path.exists():
            return

        with open(self.vault_path, 'r') as f:
            data = json.load(f)

        self.data = {
            key: EncryptedData.from_dict(encrypted_data)
            for key, encrypted_data in data.items()
        }


# Simple fallback encryption when cryptography is not available
class SimpleCipher:
    """Simple XOR cipher for basic obfuscation (NOT cryptographically secure)."""

    @staticmethod
    def encrypt(data: str, key: str) -> str:
        """Simple XOR encryption (for fallback only)."""
        key_bytes = key.encode()
        data_bytes = data.encode()
        encrypted = bytes([data_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(data_bytes))])
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt(encrypted: str, key: str) -> str:
        """Simple XOR decryption (for fallback only)."""
        key_bytes = key.encode()
        encrypted_bytes = base64.b64decode(encrypted)
        decrypted = bytes([encrypted_bytes[i] ^ key_bytes[i % len(key_bytes)] for i in range(len(encrypted_bytes))])
        return decrypted.decode('utf-8')
