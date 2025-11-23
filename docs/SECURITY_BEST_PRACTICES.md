# Security Best Practices

Security guidelines for deploying and operating Codex Prime Agent OS.

## Table of Contents

1. [API Keys & Secrets Management](#api-keys--secrets-management)
2. [Network Security](#network-security)
3. [Access Control](#access-control)
4. [Data Encryption](#data-encryption)
5. [Audit Logging](#audit-logging)
6. [Secure Deployment](#secure-deployment)
7. [Plugin Security](#plugin-security)
8. [Monitoring & Incident Response](#monitoring--incident-response)

## API Keys & Secrets Management

### ❌ DON'T

```python
# Never hardcode secrets
OPENAI_API_KEY = "sk-1234567890"
DATABASE_URL = "postgresql://user:password@localhost/db"
```

```yaml
# Never commit secrets to version control
secrets:
  openai_api_key: "sk-real-key-here"
```

### ✅ DO

```python
# Use environment variables
import os
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
```

```bash
# Use external secret management
kubectl create secret generic codex-prime-secrets \
  --from-literal=openai-api-key="${OPENAI_API_KEY}"
```

### Best Practices

1. **Use Environment Variables**
   - Store secrets in environment variables
   - Use `.env` files locally (gitignored)
   - Rotate keys regularly

2. **External Secret Management**
   - AWS Secrets Manager
   - Google Secret Manager
   - Azure Key Vault
   - HashiCorp Vault

3. **Kubernetes Secrets**
   ```yaml
   apiVersion: v1
   kind: Secret
   metadata:
     name: api-secrets
   type: Opaque
   data:
     openai-key: <base64-encoded>
   ```

4. **Secret Rotation**
   - Rotate keys every 90 days
   - Implement automated rotation where possible
   - Monitor for leaked credentials

## Network Security

### TLS/SSL Configuration

```yaml
# Enforce TLS
ingress:
  enabled: true
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
  tls:
    - secretName: codex-prime-tls
      hosts:
        - api.codex-prime.com
```

### Network Policies

```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: codex-prime-netpol
spec:
  podSelector:
    matchLabels:
      app: codex-prime-api
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
      - podSelector:
          matchLabels:
            app: web-ui
      ports:
      - protocol: TCP
        port: 8000
  egress:
    - to:
      - podSelector:
          matchLabels:
            app: postgres
      ports:
      - protocol: TCP
        port: 5432
```

### Firewall Rules

- Only expose necessary ports
- Use private networks for database connections
- Implement rate limiting
- Enable DDoS protection

## Access Control

### RBAC Configuration

```python
from codex_prime.security import RBACManager, Permission

rbac = RBACManager("~/.codex_prime/rbac.json")

# Create users with minimum necessary permissions
rbac.create_user(
    user_id="developer",
    roles=["developer"]  # Not "admin"
)

# Check permissions before operations
if rbac.check_permission(user_id, Permission.AGENT_EXECUTE):
    # Allow operation
else:
    raise PermissionError("Access denied")
```

### Default Roles

| Role | Permissions | Use Case |
|------|-------------|----------|
| `viewer` | Read-only access | Monitoring, reporting |
| `operator` | Execute agents, read memory | Day-to-day operations |
| `developer` | Full access except admin | Development |
| `admin` | All permissions | System administration |

### Principle of Least Privilege

```python
# Grant minimum necessary permissions
user_roles = ["operator"]  # Not ["admin"]

# Use scoped API keys
api_key, key_obj = api_mgr.create_key(
    name="CI/CD Key",
    scopes={"agent:execute"},  # Not {"*"}
    expires_in_days=30  # Set expiration
)
```

## Data Encryption

### At Rest

```python
from codex_prime.security import EncryptionManager, SecureVault

# Encrypt sensitive data
encryption = EncryptionManager()
vault = SecureVault("~/.codex_prime/secrets.json", encryption)

# Store encrypted
vault.store("api_key", "sk-1234567890", metadata={"service": "openai"})

# Retrieve and decrypt
api_key = vault.retrieve("api_key")
```

### In Transit

- Use HTTPS/TLS for all API communication
- Enable TLS for database connections
- Use encrypted WebSocket (WSS)

### Database Encryption

```yaml
# PostgreSQL with TLS
postgresql:
  ssl:
    enabled: true
    mode: require
```

## Audit Logging

### Enable Comprehensive Logging

```python
from codex_prime.security import AuditLogger, AuditEventType

audit = AuditLogger("~/.codex_prime/audit")

# Log all security events
audit.log_login(user_id, success=True, ip_address=request.remote_addr)
audit.log_access(user_id, resource_type, resource_id, granted=True)
audit.log_permission_change(admin_id, user_id, old_roles, new_roles)
```

### Audit Log Retention

- Retain logs for at least 90 days
- Implement log rotation
- Store logs in tamper-proof storage
- Regular log review and analysis

### What to Log

```python
# Authentication events
audit.log_login(user_id, success, ip_address, user_agent)

# Authorization events
audit.log_access(user_id, resource, action, granted)

# Data access
audit.log_data_access(user_id, data_type, record_ids)

# Configuration changes
audit.log_config_change(admin_id, setting, old_value, new_value)

# Security events
audit.log_security_event(event_type, details, severity)
```

## Secure Deployment

### Container Security

```dockerfile
# Use specific versions
FROM python:3.11-slim

# Run as non-root user
RUN useradd -m -u 1000 codex
USER codex

# Read-only filesystem where possible
# No unnecessary capabilities
```

### Kubernetes Security Context

```yaml
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  allowPrivilegeEscalation: false
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: true
```

### Image Scanning

```bash
# Scan images for vulnerabilities
trivy image codex-prime:latest

# Fail build on critical vulnerabilities
trivy image --severity CRITICAL,HIGH --exit-code 1 codex-prime:latest
```

## Plugin Security

### Security Scanning

```python
from codex_prime.plugins import SecurityScanner

scanner = SecurityScanner()
issues = scanner.scan_plugin(plugin_path)

# Block plugins with critical issues
if any(issue.severity == "critical" for issue in issues):
    raise SecurityError("Plugin has critical security issues")
```

### Plugin Sandboxing

- Run plugins in isolated environments
- Limit plugin permissions
- Monitor plugin resource usage
- Review plugin code before installation

### Whitelist Trusted Plugins

```yaml
# Only allow verified plugins
plugin_policy:
  allow_unverified: false
  trusted_publishers:
    - official
    - verified-partners
```

## Monitoring & Incident Response

### Security Monitoring

```python
from codex_prime.observability import MetricsCollector, get_logger

logger = get_logger(__name__)
metrics = MetricsCollector()

# Monitor failed login attempts
metrics.increment_counter("auth_failures", {"user_id": user_id})

if failed_attempts > 5:
    logger.warning("Multiple failed login attempts", extra={
        "user_id": user_id,
        "ip_address": ip,
        "attempts": failed_attempts
    })
```

### Alerts

Set up alerts for:
- Multiple failed authentication attempts
- Privilege escalation attempts
- Unusual data access patterns
- High rate of API calls
- Suspicious plugin installations
- Configuration changes

### Incident Response Plan

1. **Detection**: Automated monitoring and alerts
2. **Containment**: Isolate affected systems
3. **Investigation**: Review audit logs
4. **Remediation**: Patch vulnerabilities
5. **Recovery**: Restore from backups
6. **Post-Incident**: Document and improve

## Security Checklist

### Development

- [ ] No hardcoded secrets in code
- [ ] All inputs validated and sanitized
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (escape outputs)
- [ ] CSRF tokens on state-changing operations
- [ ] Secure dependencies (no known vulnerabilities)
- [ ] Security-focused code review

### Deployment

- [ ] TLS/SSL enabled for all endpoints
- [ ] Secrets in external secret manager
- [ ] RBAC configured with least privilege
- [ ] Network policies restrict traffic
- [ ] Container security scanning enabled
- [ ] Running as non-root user
- [ ] Audit logging enabled
- [ ] Regular security updates scheduled

### Operations

- [ ] Monitoring and alerting configured
- [ ] Regular security audits
- [ ] Incident response plan documented
- [ ] Regular backup testing
- [ ] API key rotation schedule
- [ ] Security training for team
- [ ] Vulnerability disclosure policy

## Compliance

### GDPR

- Implement data deletion capabilities
- Obtain user consent for data collection
- Provide data export functionality
- Document data processing activities

### HIPAA

- Enable encryption at rest and in transit
- Implement access controls and audit logging
- Business Associate Agreements with LLM providers
- Regular security assessments

### SOC 2

- Comprehensive audit logging
- Regular security testing
- Access control policies
- Incident response procedures
- Vendor management

## Security Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [CIS Kubernetes Benchmark](https://www.cisecurity.org/benchmark/kubernetes)
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [Python Security Best Practices](https://python.readthedocs.io/en/stable/library/security_warnings.html)

## Reporting Security Issues

If you discover a security vulnerability:

1. **DO NOT** create a public GitHub issue
2. Email security@codex-prime.dev
3. Include detailed description and reproduction steps
4. Allow time for investigation and patch
5. Coordinate disclosure timeline

---

**Security is everyone's responsibility. Stay vigilant!**
