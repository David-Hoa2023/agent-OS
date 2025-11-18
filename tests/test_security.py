"""Tests for security features."""

import pytest
import time
from pathlib import Path
from datetime import datetime, timedelta
from codex_prime.security import (
    # RBAC
    Role, Permission, User, RBACManager,
    # Encryption
    EncryptionManager, SecureVault, CRYPTO_AVAILABLE,
    # Audit
    AuditLogger, AuditEvent, AuditEventType, AuditSeverity,
    # API Keys
    APIKeyManager, APIKey,
    # Rate Limiting
    RateLimiter, RateLimitExceeded, SlidingWindowRateLimiter
)


# RBAC Tests

def test_role_permissions():
    """Test role permission management."""
    role = Role("developer", "Developer role")

    role.add_permission(Permission.AGENT_READ)
    role.add_permission(Permission.AGENT_WRITE)

    assert role.has_permission(Permission.AGENT_READ)
    assert role.has_permission(Permission.AGENT_WRITE)
    assert not role.has_permission(Permission.USER_MANAGE)

    role.remove_permission(Permission.AGENT_WRITE)
    assert not role.has_permission(Permission.AGENT_WRITE)


def test_user_permissions():
    """Test user permission checks."""
    developer_role = Role("developer", "Developer")
    developer_role.add_permission(Permission.AGENT_READ)
    developer_role.add_permission(Permission.AGENT_EXECUTE)

    admin_role = Role("admin", "Admin")
    admin_role.add_permission(Permission.USER_MANAGE)

    user = User(user_id="user1", username="alice", email="alice@test.com")
    user.add_role(developer_role)

    assert user.has_permission(Permission.AGENT_READ)
    assert user.has_permission(Permission.AGENT_EXECUTE)
    assert not user.has_permission(Permission.USER_MANAGE)

    # Add admin role
    user.add_role(admin_role)
    assert user.has_permission(Permission.USER_MANAGE)


def test_user_multiple_roles():
    """Test user with multiple roles."""
    role1 = Role("role1", "Role 1")
    role1.add_permission(Permission.AGENT_READ)

    role2 = Role("role2", "Role 2")
    role2.add_permission(Permission.AGENT_WRITE)

    user = User(user_id="user1", username="bob", email="bob@test.com")
    user.add_role(role1)
    user.add_role(role2)

    all_permissions = user.get_all_permissions()
    assert Permission.AGENT_READ in all_permissions
    assert Permission.AGENT_WRITE in all_permissions


def test_rbac_manager_default_roles():
    """Test RBAC manager creates default roles."""
    manager = RBACManager()

    assert "admin" in manager.roles
    assert "developer" in manager.roles
    assert "operator" in manager.roles
    assert "viewer" in manager.roles

    # Admin should have all permissions
    admin = manager.get_role("admin")
    assert admin.has_permission(Permission.USER_MANAGE)
    assert admin.has_permission(Permission.AGENT_DELETE)


def test_rbac_create_user():
    """Test creating users."""
    manager = RBACManager()

    user = manager.create_user("user1", "alice", "alice@test.com", roles=["developer"])

    assert user.user_id == "user1"
    assert user.username == "alice"
    assert len(user.roles) == 1
    assert user.has_permission(Permission.AGENT_READ)


def test_rbac_grant_revoke_role():
    """Test granting and revoking roles."""
    manager = RBACManager()

    user = manager.create_user("user1", "alice", "alice@test.com", roles=["viewer"])
    assert not user.has_permission(Permission.AGENT_WRITE)

    # Grant developer role
    manager.grant_role("user1", "developer")
    assert user.has_permission(Permission.AGENT_WRITE)

    # Revoke developer role
    manager.revoke_role("user1", "developer")
    assert not user.has_permission(Permission.AGENT_WRITE)


def test_rbac_check_permission():
    """Test permission checking."""
    manager = RBACManager()
    user = manager.create_user("user1", "alice", "alice@test.com", roles=["developer"])

    assert manager.check_permission("user1", Permission.AGENT_READ)
    assert not manager.check_permission("user1", Permission.USER_MANAGE)


def test_rbac_require_permission():
    """Test requiring permissions."""
    manager = RBACManager()
    user = manager.create_user("user1", "alice", "alice@test.com", roles=["developer"])

    # Should not raise
    manager.require_permission("user1", Permission.AGENT_READ)

    # Should raise
    with pytest.raises(PermissionError):
        manager.require_permission("user1", Permission.USER_MANAGE)


# Encryption Tests

@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography package not installed")
def test_encryption_manager():
    """Test encryption and decryption."""
    manager = EncryptionManager()

    data = "sensitive information"
    encrypted = manager.encrypt(data)

    assert encrypted.ciphertext != data
    assert encrypted.salt is not None

    decrypted = manager.decrypt(encrypted)
    assert decrypted == data


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography package not installed")
def test_encryption_with_password():
    """Test encryption with custom password."""
    manager = EncryptionManager()

    data = "secret data"
    password = "my_secure_password"

    encrypted = manager.encrypt(data, password)
    decrypted = manager.decrypt(encrypted, password)

    assert decrypted == data

    # Wrong password should fail
    with pytest.raises(ValueError):
        manager.decrypt(encrypted, "wrong_password")


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography package not installed")
def test_encryption_dict():
    """Test encrypting dictionaries."""
    manager = EncryptionManager()

    data = {"key": "value", "number": 42}
    encrypted = manager.encrypt_dict(data)
    decrypted = manager.decrypt_dict(encrypted)

    assert decrypted == data


@pytest.mark.skipif(not CRYPTO_AVAILABLE, reason="cryptography package not installed")
def test_secure_vault(tmp_path):
    """Test secure vault."""
    manager = EncryptionManager()
    vault = SecureVault(tmp_path / "vault.json", manager)

    vault.store("api_key", "sk-1234567890")
    vault.store("password", "secret123")

    assert vault.retrieve("api_key") == "sk-1234567890"
    assert vault.retrieve("password") == "secret123"

    keys = vault.list_keys()
    assert "api_key" in keys
    assert "password" in keys

    vault.delete("password")
    assert vault.retrieve("password") is None


def test_password_hashing():
    """Test password hashing."""
    password = "my_password_123"
    hash1 = EncryptionManager.hash_password(password)
    hash2 = EncryptionManager.hash_password(password)

    # Same password should produce same hash
    assert hash1 == hash2

    # Verify password
    assert EncryptionManager.verify_password(password, hash1)
    assert not EncryptionManager.verify_password("wrong_password", hash1)


# Audit Logging Tests

def test_audit_logger(tmp_path):
    """Test audit logging."""
    logger = AuditLogger(tmp_path / "audit")

    event = logger.log(
        event_type=AuditEventType.LOGIN_SUCCESS,
        user_id="user1",
        ip_address="192.168.1.1"
    )

    assert event.event_type == AuditEventType.LOGIN_SUCCESS
    assert event.user_id == "user1"
    assert event.ip_address == "192.168.1.1"


def test_audit_log_access(tmp_path):
    """Test logging access events."""
    logger = AuditLogger(tmp_path / "audit")

    # Granted access
    event1 = logger.log_access("user1", "agent", "agent123", granted=True)
    assert event1.event_type == AuditEventType.ACCESS_GRANTED
    assert event1.result == "success"

    # Denied access
    event2 = logger.log_access("user2", "agent", "agent123", granted=False)
    assert event2.event_type == AuditEventType.ACCESS_DENIED
    assert event2.result == "denied"


def test_audit_log_login(tmp_path):
    """Test logging login events."""
    logger = AuditLogger(tmp_path / "audit")

    # Successful login
    event1 = logger.log_login("user1", success=True, ip_address="192.168.1.1")
    assert event1.event_type == AuditEventType.LOGIN_SUCCESS

    # Failed login
    event2 = logger.log_login("user2", success=False, ip_address="192.168.1.2")
    assert event2.event_type == AuditEventType.LOGIN_FAILED
    assert event2.severity == AuditSeverity.WARNING


def test_audit_query(tmp_path):
    """Test querying audit events."""
    logger = AuditLogger(tmp_path / "audit")

    # Log various events
    logger.log_login("user1", success=True)
    logger.log_login("user2", success=False)
    logger.log_access("user1", "data", "data123", granted=True)

    # Query by user
    user1_events = logger.query(user_id="user1")
    assert len(user1_events) == 2

    # Query by event type
    login_events = logger.query(event_type=AuditEventType.LOGIN_SUCCESS)
    assert len(login_events) == 1

    # Query by severity
    warnings = logger.query(severity=AuditSeverity.WARNING)
    assert len(warnings) >= 1


def test_audit_security_events(tmp_path):
    """Test security event logging."""
    logger = AuditLogger(tmp_path / "audit")

    logger.log_security_violation("user1", "brute_force_attempt")
    logger.log_security_violation("user2", "sql_injection")

    security_events = logger.get_security_events(days=1)
    assert len(security_events) == 2


# API Key Tests

def test_api_key_generation():
    """Test API key generation."""
    key = APIKeyManager.generate_key()

    assert key.startswith("cpx_")
    assert len(key) > 10


def test_api_key_hashing():
    """Test API key hashing."""
    key = "cpx_test_key_123"
    hash1 = APIKeyManager.hash_key(key)
    hash2 = APIKeyManager.hash_key(key)

    assert hash1 == hash2
    assert hash1 != key


def test_api_key_manager_create():
    """Test creating API keys."""
    manager = APIKeyManager()

    api_key, key_obj = manager.create_key(
        name="Test Key",
        user_id="user1",
        scopes={"read", "write"}
    )

    assert api_key.startswith("cpx_")
    assert key_obj.name == "Test Key"
    assert key_obj.user_id == "user1"
    assert key_obj.has_scope("read")
    assert key_obj.has_scope("write")


def test_api_key_validation():
    """Test API key validation."""
    manager = APIKeyManager()

    api_key, key_obj = manager.create_key("Test Key", "user1")

    # Valid key
    validated = manager.validate_key(api_key)
    assert validated is not None
    assert validated.key_id == key_obj.key_id

    # Invalid key
    invalid = manager.validate_key("cpx_invalid_key")
    assert invalid is None


def test_api_key_revoke():
    """Test revoking API keys."""
    manager = APIKeyManager()

    api_key, key_obj = manager.create_key("Test Key", "user1")

    # Key should be valid
    assert manager.validate_key(api_key) is not None

    # Revoke key
    manager.revoke_key(key_obj.key_id)

    # Key should be invalid
    assert manager.validate_key(api_key) is None


def test_api_key_expiration():
    """Test API key expiration."""
    manager = APIKeyManager()

    # Create key that expires in 1 day
    api_key, key_obj = manager.create_key(
        "Test Key",
        "user1",
        expires_in_days=1
    )

    assert key_obj.expires_at is not None
    assert key_obj.is_valid()

    # Simulate expiration
    key_obj.expires_at = datetime.now() - timedelta(days=1)
    assert not key_obj.is_valid()


def test_api_key_rotation():
    """Test API key rotation."""
    manager = APIKeyManager()

    old_key, old_obj = manager.create_key("Test Key", "user1", scopes={"read"})

    # Rotate key
    new_key, new_obj = manager.rotate_key(old_obj.key_id)

    # New key should be valid
    assert manager.validate_key(new_key) is not None

    # Old key should be revoked
    assert manager.validate_key(old_key) is None

    # New key should have same scopes
    assert new_obj.has_scope("read")


# Rate Limiting Tests

def test_rate_limiter_basic():
    """Test basic rate limiting."""
    limiter = RateLimiter(default_limit=5, default_window=10)

    # Should allow 5 requests
    for _ in range(5):
        info = limiter.consume("user1")
        assert info.remaining >= 0

    # 6th request should fail
    with pytest.raises(RateLimitExceeded):
        limiter.consume("user1")


def test_rate_limiter_refill():
    """Test token refill."""
    limiter = RateLimiter(default_limit=2, default_window=1)

    # Consume all tokens
    limiter.consume("user1")
    limiter.consume("user1")

    # Should fail
    with pytest.raises(RateLimitExceeded):
        limiter.consume("user1")

    # Wait for refill
    time.sleep(1.1)

    # Should work again
    info = limiter.consume("user1")
    assert info.remaining >= 0


def test_rate_limiter_custom_limits():
    """Test custom rate limits."""
    limiter = RateLimiter(default_limit=10, default_window=60)

    # Set custom limit for premium user
    limiter.set_limit("premium_user", limit=100, window=60)

    # Premium user should have higher limit
    info = limiter.check_limit("premium_user")
    assert info.limit == 100

    # Regular user should have default limit
    info = limiter.check_limit("regular_user")
    assert info.limit == 10


def test_rate_limiter_reset():
    """Test resetting rate limit."""
    limiter = RateLimiter(default_limit=2, default_window=10)

    # Consume tokens
    limiter.consume("user1")
    limiter.consume("user1")

    # Should fail
    with pytest.raises(RateLimitExceeded):
        limiter.consume("user1")

    # Reset
    limiter.reset("user1")

    # Should work again
    info = limiter.consume("user1")
    assert info.remaining >= 0


def test_sliding_window_rate_limiter():
    """Test sliding window rate limiter."""
    limiter = SlidingWindowRateLimiter(default_limit=3, default_window=2)

    # Allow 3 requests
    for _ in range(3):
        info = limiter.consume("user1")
        assert info.remaining >= 0

    # 4th should fail
    with pytest.raises(RateLimitExceeded):
        limiter.consume("user1")

    # Wait for window to slide
    time.sleep(2.1)

    # Should work again
    info = limiter.consume("user1")
    assert info.remaining >= 0


def test_rate_limiter_multiple_users():
    """Test rate limiting for multiple users."""
    limiter = RateLimiter(default_limit=2, default_window=10)

    # User 1 consumes tokens
    limiter.consume("user1")
    limiter.consume("user1")

    # User 1 should be blocked
    with pytest.raises(RateLimitExceeded):
        limiter.consume("user1")

    # User 2 should still work
    info = limiter.consume("user2")
    assert info.remaining >= 0
