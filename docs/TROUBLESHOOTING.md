# Troubleshooting Guide

Comprehensive solutions to common issues with Codex Prime Agent OS.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Installation Issues](#installation-issues)
3. [Runtime Errors](#runtime-errors)
4. [Memory & Storage Issues](#memory--storage-issues)
5. [LLM Provider Issues](#llm-provider-issues)
6. [Plugin Issues](#plugin-issues)
7. [Performance Problems](#performance-problems)
8. [Deployment Issues](#deployment-issues)
9. [Security & Access Control](#security--access-control)
10. [FAQ](#faq)

## Quick Diagnostics

Run these commands to gather diagnostic information:

```bash
# Check system status
python -c "from codex_prime.core import AgentOS; print(AgentOS.version())"

# Verify dependencies
pip check

# Test basic functionality
python -m codex_prime.tests.test_core

# Check environment variables
env | grep -E "(OPENAI|ANTHROPIC|CODEX)"

# View recent logs
tail -f ~/.codex_prime/logs/agent.log
```

### Health Check Script

```python
from codex_prime.core import AgentOS
from codex_prime.memory import MemoryVault
from codex_prime.tools import ToolRegistry
import os

def health_check():
    """Run comprehensive health check"""

    print("🔍 Running Health Check...\n")

    # Check API keys
    print("1. API Keys:")
    print(f"   OpenAI: {'✅' if os.getenv('OPENAI_API_KEY') else '❌'}")
    print(f"   Anthropic: {'✅' if os.getenv('ANTHROPIC_API_KEY') else '❌'}")

    # Check filesystem
    print("\n2. File System:")
    workspace = Path.home() / ".codex_prime"
    print(f"   Workspace exists: {'✅' if workspace.exists() else '❌'}")
    print(f"   Writable: {'✅' if os.access(workspace, os.W_OK) else '❌'}")

    # Check memory vault
    print("\n3. Memory Vault:")
    try:
        vault = MemoryVault()
        print(f"   Initialized: ✅")
        stats = vault.get_stats()
        print(f"   Total memories: {stats['total_memories']}")
    except Exception as e:
        print(f"   Error: ❌ {e}")

    # Check tools
    print("\n4. Tool Registry:")
    try:
        registry = ToolRegistry()
        tools = registry.list_tools()
        print(f"   Available tools: {len(tools)}")
    except Exception as e:
        print(f"   Error: ❌ {e}")

    print("\n✅ Health check complete!")

if __name__ == "__main__":
    health_check()
```

## Installation Issues

### Issue: `pip install` fails with dependency conflicts

**Symptoms:**
```
ERROR: pip's dependency resolver does not currently take into account all the packages that are installed.
```

**Solutions:**

```bash
# Solution 1: Use fresh virtual environment
python -m venv venv_fresh
source venv_fresh/bin/activate
pip install codex-prime

# Solution 2: Upgrade pip
pip install --upgrade pip setuptools wheel

# Solution 3: Install with --no-deps and resolve manually
pip install --no-deps codex-prime
pip install -r requirements.txt
```

### Issue: ChromaDB installation fails

**Symptoms:**
```
ERROR: Could not build wheels for chroma-hnswlib
```

**Solutions:**

```bash
# macOS
brew install cmake
pip install chromadb

# Ubuntu/Debian
sudo apt-get install cmake build-essential
pip install chromadb

# Windows
# Install Visual Studio Build Tools
# Then: pip install chromadb
```

### Issue: Import errors after installation

**Symptoms:**
```python
ImportError: cannot import name 'AgentOS' from 'codex_prime.core'
```

**Solutions:**

```bash
# Verify installation
pip show codex-prime

# Reinstall in development mode
pip uninstall codex-prime
pip install -e .

# Clear Python cache
find . -type d -name __pycache__ -exec rm -r {} +
python -m pip cache purge
```

## Runtime Errors

### Issue: Agent fails to initialize

**Symptoms:**
```
AgentInitializationError: Failed to initialize agent workspace
```

**Diagnostic:**
```python
import logging
logging.basicConfig(level=logging.DEBUG)

from codex_prime.core import AgentOS

agent = AgentOS(
    project_name="test",
    workspace="./test_workspace"
)
```

**Solutions:**

1. **Check permissions:**
```bash
# Verify workspace is writable
mkdir -p ~/.codex_prime
touch ~/.codex_prime/test_file
rm ~/.codex_prime/test_file
```

2. **Clear corrupted state:**
```bash
# Backup and reset
mv ~/.codex_prime ~/.codex_prime.backup
mkdir ~/.codex_prime
```

3. **Check disk space:**
```bash
df -h ~/.codex_prime
```

### Issue: `ToolExecutionError`

**Symptoms:**
```
ToolExecutionError: Tool 'web_search' failed with error: Connection timeout
```

**Solutions:**

```python
# 1. Check tool configuration
from codex_prime.tools import ToolRegistry

registry = ToolRegistry()
tool = registry.get_tool("web_search")
print(tool.config)

# 2. Set timeout
tool.config["timeout"] = 60  # seconds

# 3. Test tool directly
result = tool.execute(query="test", timeout=30)
```

### Issue: Memory recall returns no results

**Symptoms:**
```python
results = vault.recall("query")
# returns []
```

**Diagnostic:**
```python
from codex_prime.memory import MemoryVault

vault = MemoryVault()

# Check stats
stats = vault.get_stats()
print(f"Total memories: {stats['total_memories']}")
print(f"Tiers: {stats['tiers']}")

# List all memories
all_memories = vault.list_memories()
print(f"Found {len(all_memories)} memories")

# Check embedding service
embeddings = vault.embedding_model.embed(["test query"])
print(f"Embedding dimension: {len(embeddings[0])}")
```

**Solutions:**

```python
# 1. Re-index memories
vault.reindex()

# 2. Lower similarity threshold
results = vault.recall("query", threshold=0.3)

# 3. Check tier
results = vault.recall("query", tier="short_term")

# 4. Use tags
results = vault.recall("query", tags=["important"])
```

## Memory & Storage Issues

### Issue: High memory usage

**Symptoms:**
- Agent process using >4GB RAM
- System becomes sluggish

**Diagnostic:**
```python
import psutil
import os

process = psutil.Process(os.getpid())
print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

# Profile memory
from memory_profiler import profile

@profile
def run_agent():
    agent = AgentOS(project_name="test", workspace="./test")
    agent.execute("Analyze data")
```

**Solutions:**

1. **Limit memory cache:**
```python
from codex_prime.memory import MemoryVault

vault = MemoryVault(
    cache_size=1000,  # Limit cache entries
    max_memory_mb=512  # Set memory limit
)
```

2. **Use batch processing:**
```python
# Instead of loading all at once
memories = vault.list_memories()

# Process in batches
for batch in vault.batch_memories(batch_size=100):
    process_batch(batch)
```

3. **Clear old memories:**
```python
from datetime import datetime, timedelta

# Archive memories older than 30 days
cutoff = datetime.now() - timedelta(days=30)
vault.archive_before(cutoff)
```

### Issue: Disk space exhaustion

**Symptoms:**
```
OSError: [Errno 28] No space left on device
```

**Check usage:**
```bash
# Check workspace size
du -sh ~/.codex_prime/*

# Find large files
find ~/.codex_prime -type f -size +100M -exec ls -lh {} \;
```

**Solutions:**

```bash
# 1. Clean logs
find ~/.codex_prime/logs -type f -mtime +30 -delete

# 2. Compress old data
tar -czf archive_$(date +%Y%m%d).tar.gz ~/.codex_prime/archive/
rm -rf ~/.codex_prime/archive/*

# 3. Clean ChromaDB
python -c "from codex_prime.memory import MemoryVault; MemoryVault().vacuum()"
```

## LLM Provider Issues

### Issue: OpenAI API errors

**Symptoms:**
```
openai.error.RateLimitError: Rate limit reached
openai.error.InvalidRequestError: Invalid API key
```

**Solutions:**

1. **Verify API key:**
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

2. **Handle rate limits:**
```python
from codex_prime.llm import OpenAIProvider

provider = OpenAIProvider(
    api_key=os.getenv("OPENAI_API_KEY"),
    max_retries=5,
    retry_delay=2.0,
    rate_limit_strategy="exponential_backoff"
)
```

3. **Switch models:**
```python
# Use different model
agent = AgentOS(
    project_name="test",
    provider="openai",
    model="gpt-3.5-turbo"  # Instead of gpt-4
)
```

### Issue: Anthropic API timeouts

**Symptoms:**
```
ReadTimeout: Request to Anthropic API timed out
```

**Solutions:**

```python
from codex_prime.llm import AnthropicProvider

provider = AnthropicProvider(
    api_key=os.getenv("ANTHROPIC_API_KEY"),
    timeout=120,  # Increase timeout
    max_tokens_to_sample=2048  # Reduce for faster responses
)

# Test connection
response = provider.generate(
    prompt="Hello",
    max_tokens=10
)
print(response)
```

### Issue: Context length exceeded

**Symptoms:**
```
InvalidRequestError: This model's maximum context length is 4096 tokens
```

**Solutions:**

```python
# 1. Use summarization
from codex_prime.memory import MemoryVault

vault = MemoryVault()
memories = vault.recall("query", k=5)  # Limit results

# Summarize context
summarized = agent.summarize(memories)

# 2. Chunk large inputs
def chunk_text(text, chunk_size=2000):
    words = text.split()
    for i in range(0, len(words), chunk_size):
        yield ' '.join(words[i:i + chunk_size])

for chunk in chunk_text(large_text):
    result = agent.execute(chunk)

# 3. Use models with larger context
agent = AgentOS(
    project_name="test",
    provider="anthropic",
    model="claude-2"  # 100k context window
)
```

## Plugin Issues

### Issue: Plugin fails to load

**Symptoms:**
```
PluginLoadError: Failed to load plugin 'my-plugin'
```

**Diagnostic:**
```python
from codex_prime.plugins import PluginManager

manager = PluginManager()

# Check plugin
try:
    plugin = manager.load_plugin("my-plugin")
    print(f"Loaded: {plugin}")
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()

# Validate plugin
from codex_prime.plugins import PluginValidator

validator = PluginValidator()
issues = validator.validate_plugin("plugins/my-plugin")
for issue in issues:
    print(f"{issue.severity}: {issue.message}")
```

**Solutions:**

1. **Check plugin structure:**
```bash
# Verify required files
ls -la plugins/my-plugin/
# Should have: plugin.json, __init__.py, etc.
```

2. **Validate plugin.json:**
```python
import json

with open("plugins/my-plugin/plugin.json") as f:
    config = json.load(f)

required = ["name", "version", "entry_point", "type"]
for field in required:
    if field not in config:
        print(f"Missing required field: {field}")
```

3. **Check dependencies:**
```bash
# Install plugin dependencies
pip install -r plugins/my-plugin/requirements.txt
```

### Issue: Plugin security scan fails

**Symptoms:**
```
SecurityError: Plugin contains critical security issues
```

**Review issues:**
```python
from codex_prime.plugins import SecurityScanner

scanner = SecurityScanner()
issues = scanner.scan_plugin("plugins/my-plugin")

for issue in issues:
    print(f"{issue.severity}: {issue.rule}")
    print(f"  Location: {issue.file}:{issue.line}")
    print(f"  Description: {issue.description}\n")
```

**Common fixes:**
- Remove hardcoded secrets
- Use parameterized queries (no SQL injection)
- Validate all user inputs
- Use safe file operations (no path traversal)

## Performance Problems

### Issue: Slow agent responses

**Diagnostic:**
```python
import time
from codex_prime.core import AgentOS

agent = AgentOS(project_name="test", workspace="./test")

# Measure execution time
start = time.time()
result = agent.execute("Analyze this data")
elapsed = time.time() - start

print(f"Execution time: {elapsed:.2f}s")

# Profile with cProfile
import cProfile
cProfile.run('agent.execute("task")', sort='cumulative')
```

**Solutions:**

1. **Enable caching:**
```python
from codex_prime.core import AgentOS

agent = AgentOS(
    project_name="test",
    workspace="./test",
    enable_cache=True,
    cache_ttl=3600  # 1 hour
)
```

2. **Use async execution:**
```python
import asyncio
from codex_prime.core import AgentOS

async def run_parallel():
    agent = AgentOS(project_name="test", workspace="./test")

    tasks = [
        agent.execute_async("task1"),
        agent.execute_async("task2"),
        agent.execute_async("task3")
    ]

    results = await asyncio.gather(*tasks)
    return results

results = asyncio.run(run_parallel())
```

3. **Optimize memory recall:**
```python
# Limit recall results
vault.recall(query, k=5)  # Instead of default 10

# Use approximate search
vault.recall(query, approximate=True)

# Cache embeddings
vault.enable_embedding_cache()
```

### Issue: High API costs

**Monitor usage:**
```python
from codex_prime.observability import MetricsCollector

metrics = MetricsCollector()

# Track API calls
print(f"Total API calls: {metrics.get_counter('llm.api_calls')}")
print(f"Total tokens: {metrics.get_counter('llm.tokens_used')}")
print(f"Estimated cost: ${metrics.get_gauge('llm.estimated_cost'):.2f}")
```

**Solutions:**

```python
# 1. Use cheaper models for simple tasks
agent.set_model_for_task("summarization", "gpt-3.5-turbo")
agent.set_model_for_task("complex_reasoning", "gpt-4")

# 2. Implement response caching
from codex_prime.llm import ResponseCache

cache = ResponseCache(ttl=3600)
agent.enable_response_cache(cache)

# 3. Reduce token usage
agent.config.max_tokens = 512  # Lower limit
agent.config.temperature = 0.7  # More focused responses

# 4. Batch requests
results = agent.execute_batch([
    "task1",
    "task2",
    "task3"
])
```

## Deployment Issues

### Issue: Docker container crashes

**Check logs:**
```bash
# View container logs
docker logs codex-prime-api

# Check resource limits
docker stats codex-prime-api

# Inspect container
docker inspect codex-prime-api
```

**Solutions:**

1. **Increase memory limits:**
```yaml
# docker-compose.yml
services:
  api:
    mem_limit: 4g
    memswap_limit: 4g
```

2. **Fix health check:**
```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1
```

3. **Check environment variables:**
```bash
# Verify secrets are passed
docker exec codex-prime-api env | grep API_KEY
```

### Issue: Kubernetes pod not starting

**Diagnostic:**
```bash
# Check pod status
kubectl get pods -n codex-prime

# Describe pod
kubectl describe pod codex-prime-api-xyz -n codex-prime

# View logs
kubectl logs codex-prime-api-xyz -n codex-prime

# Check events
kubectl get events -n codex-prime --sort-by='.lastTimestamp'
```

**Common issues:**

1. **Image pull errors:**
```bash
# Check image
kubectl describe pod codex-prime-api-xyz -n codex-prime | grep -A5 "Events"

# Solution: Update image pull secret
kubectl create secret docker-registry regcred \
  --docker-server=<registry> \
  --docker-username=<user> \
  --docker-password=<password>
```

2. **Resource limits:**
```yaml
# Increase limits in deployment.yaml
resources:
  requests:
    memory: "1Gi"
    cpu: "500m"
  limits:
    memory: "4Gi"
    cpu: "2000m"
```

3. **Persistent volume issues:**
```bash
# Check PVC status
kubectl get pvc -n codex-prime

# Describe PVC
kubectl describe pvc codex-prime-data -n codex-prime

# Check storage class
kubectl get storageclass
```

### Issue: Ingress not routing traffic

**Check ingress:**
```bash
# View ingress
kubectl get ingress -n codex-prime

# Describe ingress
kubectl describe ingress codex-prime-ingress -n codex-prime

# Check ingress controller logs
kubectl logs -n ingress-nginx deployment/ingress-nginx-controller
```

**Solutions:**

```yaml
# Verify ingress configuration
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: codex-prime-ingress
  annotations:
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
spec:
  ingressClassName: nginx
  rules:
    - host: api.yourdomain.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: codex-prime-api
                port:
                  number: 80
```

## Security & Access Control

### Issue: Authentication failures

**Symptoms:**
```
AuthenticationError: Invalid API key
```

**Diagnostic:**
```python
from codex_prime.security import APIKeyManager

manager = APIKeyManager()

# List API keys
keys = manager.list_keys()
for key in keys:
    print(f"{key.name}: {key.scopes}, expires: {key.expires_at}")

# Verify key
is_valid = manager.verify_key("cdk_...")
print(f"Key valid: {is_valid}")
```

**Solutions:**

```python
# 1. Create new API key
from codex_prime.security import APIKeyManager

manager = APIKeyManager()
api_key, key_obj = manager.create_key(
    name="My App",
    scopes={"agent:execute", "memory:read"},
    expires_in_days=90
)
print(f"New API key: {api_key}")

# 2. Revoke and recreate
manager.revoke_key("old-key-id")
new_key, _ = manager.create_key(name="Replacement")

# 3. Check key expiration
key = manager.get_key("key-id")
if key.is_expired():
    print("Key expired, creating new one")
    new_key, _ = manager.create_key(name=key.name)
```

### Issue: Permission denied

**Symptoms:**
```
PermissionError: User 'john' does not have permission 'agent:execute'
```

**Check permissions:**
```python
from codex_prime.security import RBACManager

rbac = RBACManager()

# Check user permissions
user_id = "john"
permissions = rbac.get_user_permissions(user_id)
print(f"Permissions: {permissions}")

# Check specific permission
has_perm = rbac.check_permission(user_id, "agent:execute")
print(f"Can execute: {has_perm}")
```

**Solutions:**

```python
# Grant required permissions
rbac.add_role_to_user(user_id, "operator")

# Or create custom role
rbac.create_role(
    role_id="custom-executor",
    permissions=["agent:execute", "memory:read"]
)
rbac.add_role_to_user(user_id, "custom-executor")
```

## FAQ

### Q: How do I migrate from version X to Y?

**A:** Check the migration guide:

```bash
# View changelog
cat CHANGELOG.md

# Backup data
cp -r ~/.codex_prime ~/.codex_prime.backup

# Upgrade
pip install --upgrade codex-prime

# Run migrations
python -m codex_prime.migrate --from X --to Y
```

### Q: Can I use multiple LLM providers simultaneously?

**A:** Yes, configure provider routing:

```python
from codex_prime.core import AgentOS

agent = AgentOS(
    project_name="multi-provider",
    workspace="./workspace",
    providers={
        "fast": {"provider": "openai", "model": "gpt-3.5-turbo"},
        "smart": {"provider": "openai", "model": "gpt-4"},
        "long": {"provider": "anthropic", "model": "claude-2"}
    }
)

# Use specific provider
agent.execute("Simple task", provider="fast")
agent.execute("Complex reasoning", provider="smart")
agent.execute("Long document analysis", provider="long")
```

### Q: How do I backup and restore my agent?

**A:** Use the backup utility:

```bash
# Backup
python -m codex_prime.backup create \
  --workspace ~/.codex_prime \
  --output ./backups/backup_$(date +%Y%m%d).tar.gz

# Restore
python -m codex_prime.backup restore \
  --input ./backups/backup_20240101.tar.gz \
  --workspace ~/.codex_prime
```

### Q: How do I enable debug logging?

**A:** Configure logging level:

```python
import logging
from codex_prime.core import AgentOS

# Enable debug logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('agent_debug.log'),
        logging.StreamHandler()
    ]
)

agent = AgentOS(project_name="test", workspace="./test")
```

### Q: How do I clear all data and start fresh?

**A:** Reset workspace:

```bash
# Backup first!
mv ~/.codex_prime ~/.codex_prime.backup

# Or use reset command
python -m codex_prime.reset --confirm

# Verify
python -c "from codex_prime.core import AgentOS; a = AgentOS('test', './test')"
```

### Q: What are the minimum system requirements?

**A:**

- **CPU:** 2+ cores (4+ recommended)
- **RAM:** 4GB minimum (8GB+ recommended)
- **Storage:** 10GB minimum (50GB+ for production)
- **Python:** 3.9+
- **OS:** Linux, macOS, Windows (WSL2)
- **Network:** Internet connection for LLM APIs

### Q: How do I contribute a plugin?

**A:** Follow the plugin submission guide:

1. Develop plugin using [PLUGIN_DEVELOPMENT.md](./PLUGIN_DEVELOPMENT.md)
2. Test thoroughly with test suite
3. Run security scan
4. Submit via GitHub issue using plugin submission template
5. Wait for review and approval

### Q: How do I report a security vulnerability?

**A:** Follow responsible disclosure:

1. **DO NOT** create public GitHub issue
2. Email security@codex-prime.dev
3. Include detailed description and reproduction steps
4. Allow time for investigation and patch
5. Coordinate disclosure timeline

## Getting Help

If you're still experiencing issues:

1. **Check Documentation:** [docs.codex-prime.dev](https://docs.codex-prime.dev)
2. **Search Issues:** [GitHub Issues](https://github.com/yourusername/agent-OS/issues)
3. **Ask Community:** [GitHub Discussions](https://github.com/yourusername/agent-OS/discussions)
4. **Report Bug:** Use bug report template in `.github/ISSUE_TEMPLATE/`

**When reporting issues, include:**
- Codex Prime version
- Python version
- Operating system
- Full error message and traceback
- Steps to reproduce
- Relevant configuration

---

**Need immediate help?** Run the health check script at the top of this guide to diagnose common issues automatically.
