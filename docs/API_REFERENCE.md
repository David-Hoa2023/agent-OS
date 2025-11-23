# Codex Prime API Reference

Complete API reference for all Codex Prime modules and classes.

## Table of Contents

- [Core Modules](#core-modules)
- [Memory System](#memory-system)
- [Tool System](#tool-system)
- [Provider System](#provider-system)
- [Security & Access Control](#security--access-control)
- [Observability](#observability)
- [Multi-Agent Orchestration](#multi-agent-orchestration)
- [Workflow Automation](#workflow-automation)
- [Plugin System](#plugin-system)
- [Reasoning Modules](#reasoning-modules)
- [Domain Agents](#domain-agents)

---

## Core Modules

### AgentOS

Main agent operating system class.

```python
from codex_prime import AgentOS
```

#### Constructor

```python
AgentOS(
    project_name: str,
    workspace: Path,
    persona_path: Optional[Path] = None,
    provider: Optional[str] = "openai",
    **kwargs
)
```

**Parameters:**
- `project_name` (str): Name of the project
- `workspace` (Path): Path to workspace directory
- `persona_path` (Path, optional): Path to persona YAML file
- `provider` (str, optional): LLM provider name. Default: "openai"
- `**kwargs`: Additional configuration options

**Returns:** AgentOS instance

**Example:**
```python
from pathlib import Path
from codex_prime import AgentOS

agent = AgentOS(
    project_name="my_project",
    workspace=Path("~/.codex_prime/workspace").expanduser(),
    persona_path=Path("personas/codex_prime.yaml"),
    provider="anthropic"
)
```

#### Methods

##### execute()

Execute a task with the agent.

```python
def execute(
    self,
    task: str,
    context: Optional[Dict[str, Any]] = None,
    tools: Optional[List[str]] = None,
    **kwargs
) -> str
```

**Parameters:**
- `task` (str): Task description or prompt
- `context` (dict, optional): Additional context for the task
- `tools` (list, optional): List of tool names to make available
- `**kwargs`: Additional execution options

**Returns:** str - Agent response

**Example:**
```python
response = agent.execute(
    task="Analyze the code in src/main.py and suggest improvements",
    tools=["read_file", "execute_python"]
)
```

---

## Memory System

### MemoryVault

Three-tier memory system (Embers, Runes, Glyphs).

```python
from codex_prime.memory import MemoryVault
```

#### Constructor

```python
MemoryVault(storage_path: Path)
```

**Parameters:**
- `storage_path` (Path): Directory for memory storage

**Example:**
```python
from pathlib import Path
from codex_prime.memory import MemoryVault

vault = MemoryVault(Path("~/.codex_prime/vault").expanduser())
```

#### Methods

##### add_ember()

Add short-term memory (ember).

```python
def add_ember(
    self,
    text: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

**Parameters:**
- `text` (str): Memory content
- `tags` (list, optional): Tags for categorization
- `metadata` (dict, optional): Additional metadata

**Returns:** str - Memory ID

**Example:**
```python
memory_id = vault.add_ember(
    text="User prefers dark mode",
    tags=["preference", "ui"],
    metadata={"priority": "high"}
)
```

##### add_rune()

Add working memory (rune).

```python
def add_rune(
    self,
    text: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

##### add_glyph()

Add long-term memory (glyph).

```python
def add_glyph(
    self,
    text: str,
    tags: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> str
```

##### recall()

Retrieve memories by query.

```python
def recall(
    self,
    query: str,
    tier: Optional[str] = None,
    k: int = 10,
    tags: Optional[List[str]] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `query` (str): Search query
- `tier` (str, optional): Memory tier ("ember", "rune", "glyph")
- `k` (int): Maximum results. Default: 10
- `tags` (list, optional): Filter by tags

**Returns:** List of memory dictionaries

**Example:**
```python
results = vault.recall(
    query="dark mode preferences",
    tier="ember",
    k=5
)

for memory in results:
    print(f"[{memory['score']:.2f}] {memory['text']}")
```

### EnhancedMemoryVault

Extended memory vault with vector search.

```python
from codex_prime.memory import EnhancedMemoryVault
```

#### Constructor

```python
EnhancedMemoryVault(
    storage_path: Path,
    use_vector_search: bool = True,
    embedding_model: str = "all-MiniLM-L6-v2"
)
```

**Parameters:**
- `storage_path` (Path): Directory for memory storage
- `use_vector_search` (bool): Enable vector search. Default: True
- `embedding_model` (str): Model for embeddings

**Example:**
```python
vault = EnhancedMemoryVault(
    storage_path=Path("~/.codex_prime/vault").expanduser(),
    use_vector_search=True
)
```

#### Methods

##### semantic_search()

Perform semantic similarity search.

```python
def semantic_search(
    self,
    query: str,
    k: int = 10,
    tier: Optional[str] = None
) -> List[Dict[str, Any]]
```

**Parameters:**
- `query` (str): Search query
- `k` (int): Number of results. Default: 10
- `tier` (str, optional): Filter by tier

**Returns:** List of memory dictionaries with similarity scores

**Example:**
```python
results = vault.semantic_search(
    query="What database should I use?",
    k=5
)
```

---

## Tool System

### ToolRegistry

Registry for managing tools.

```python
from codex_prime.tools import ToolRegistry
```

#### Constructor

```python
ToolRegistry()
```

#### Methods

##### register()

Register a tool.

```python
def register(self, tool: BaseTool) -> None
```

**Parameters:**
- `tool` (BaseTool): Tool instance to register

**Example:**
```python
from codex_prime.tools import ToolRegistry
from codex_prime.tools.builtin import create_default_toolset

registry = ToolRegistry()
for tool in create_default_toolset():
    registry.register(tool)
```

##### get()

Get a tool by name.

```python
def get(self, tool_name: str) -> Optional[BaseTool]
```

##### list_tools()

List all registered tools.

```python
def list_tools() -> List[str]
```

### ToolExecutor

Executes tools with error handling and retries.

```python
from codex_prime.tools import ToolExecutor
```

#### Constructor

```python
ToolExecutor(
    registry: ToolRegistry,
    max_retries: int = 3,
    timeout: int = 30
)
```

**Parameters:**
- `registry` (ToolRegistry): Tool registry
- `max_retries` (int): Maximum retry attempts. Default: 3
- `timeout` (int): Execution timeout in seconds. Default: 30

#### Methods

##### execute()

Execute a tool.

```python
def execute(
    self,
    tool_name: str,
    parameters: Dict[str, Any],
    retry_on_failure: bool = True
) -> Dict[str, Any]
```

**Parameters:**
- `tool_name` (str): Name of tool to execute
- `parameters` (dict): Tool parameters
- `retry_on_failure` (bool): Whether to retry on failure

**Returns:** dict - Execution result

**Example:**
```python
from codex_prime.tools import ToolRegistry, ToolExecutor
from codex_prime.tools.builtin import create_default_toolset

registry = ToolRegistry()
for tool in create_default_toolset():
    registry.register(tool)

executor = ToolExecutor(registry)

# Execute Python code
result = executor.execute("execute_python", {
    "code": "print('Hello, World!')"
})
print(result['stdout'])  # "Hello, World!"

# Read file
result = executor.execute("read_file", {
    "path": "/path/to/file.txt"
})
print(result['content'])
```

### Built-in Tools

#### execute_python

Execute Python code in sandboxed environment.

**Parameters:**
- `code` (str): Python code to execute
- `timeout` (int, optional): Execution timeout

**Returns:**
- `stdout` (str): Standard output
- `stderr` (str): Standard error
- `return_value` (any): Returned value

#### execute_bash

Execute Bash commands.

**Parameters:**
- `command` (str): Bash command
- `timeout` (int, optional): Execution timeout

**Returns:**
- `stdout` (str): Standard output
- `stderr` (str): Standard error
- `exit_code` (int): Exit code

#### read_file

Read file contents.

**Parameters:**
- `path` (str): File path

**Returns:**
- `content` (str): File contents

#### write_file

Write to file.

**Parameters:**
- `path` (str): File path
- `content` (str): Content to write

**Returns:**
- `success` (bool): Operation success

---

## Provider System

### ProviderRouter

Intelligent routing between LLM providers.

```python
from codex_prime.providers import ProviderRouter, TaskComplexity
```

#### Constructor

```python
ProviderRouter(
    providers: List[BaseProvider],
    fallback_enabled: bool = True
)
```

#### Methods

##### chat()

Generate chat completion with automatic provider selection.

```python
def chat(
    self,
    messages: List[Dict[str, str]],
    complexity: TaskComplexity = TaskComplexity.MEDIUM,
    **kwargs
) -> str
```

**Parameters:**
- `messages` (list): Chat messages
- `complexity` (TaskComplexity): Task complexity level
- `**kwargs`: Additional parameters

**Returns:** str - Generated response

**Example:**
```python
from codex_prime.providers import create_default_router, TaskComplexity

router = create_default_router()

# Simple task - uses cheap model
response = router.chat(
    messages=[{"role": "user", "content": "What is 2+2?"}],
    complexity=TaskComplexity.SIMPLE
)

# Complex task - uses premium model
response = router.chat(
    messages=[{"role": "user", "content": "Design a distributed system"}],
    complexity=TaskComplexity.COMPLEX
)
```

---

## Security & Access Control

### RBACManager

Role-based access control.

```python
from codex_prime.security import RBACManager, Permission
```

#### Constructor

```python
RBACManager(config_path: Path)
```

#### Methods

##### create_user()

Create new user.

```python
def create_user(
    self,
    user_id: str,
    name: str,
    email: str,
    roles: List[str]
) -> User
```

**Example:**
```python
from pathlib import Path
from codex_prime.security import RBACManager

rbac = RBACManager(Path("~/.codex_prime/rbac.json").expanduser())

user = rbac.create_user(
    user_id="alice",
    name="Alice Smith",
    email="alice@example.com",
    roles=["developer"]
)
```

##### check_permission()

Check if user has permission.

```python
def check_permission(
    self,
    user_id: str,
    permission: Permission
) -> bool
```

**Example:**
```python
from codex_prime.security import Permission

if rbac.check_permission("alice", Permission.AGENT_EXECUTE):
    print("Alice can execute agents")
```

### EncryptionManager

Data encryption utilities.

```python
from codex_prime.security import EncryptionManager
```

#### Methods

##### encrypt()

Encrypt data.

```python
def encrypt(self, data: str) -> bytes
```

##### decrypt()

Decrypt data.

```python
def decrypt(self, encrypted_data: bytes) -> str
```

**Example:**
```python
from codex_prime.security import EncryptionManager

encryption = EncryptionManager()

# Encrypt
encrypted = encryption.encrypt("sensitive data")

# Decrypt
decrypted = encryption.decrypt(encrypted)
```

---

## Observability

### Logger

Structured JSON logging.

```python
from codex_prime.observability import get_logger
```

**Example:**
```python
logger = get_logger(__name__)

logger.info("Processing request", extra={
    "user_id": "alice",
    "request_id": "req-123"
})

logger.error("Failed to process", extra={
    "error": str(error),
    "stack_trace": traceback.format_exc()
})
```

### MetricsCollector

Prometheus metrics collection.

```python
from codex_prime.observability import MetricsCollector
```

#### Methods

##### increment_counter()

Increment counter metric.

```python
def increment_counter(
    self,
    name: str,
    labels: Optional[Dict[str, str]] = None
) -> None
```

**Example:**
```python
from codex_prime.observability import MetricsCollector

metrics = MetricsCollector()

metrics.increment_counter("api_requests_total", {
    "method": "POST",
    "endpoint": "/chat"
})
```

---

## Multi-Agent Orchestration

### MultiAgentCoordinator

Coordinate multiple agents.

```python
from codex_prime.orchestration import MultiAgentCoordinator
```

#### Constructor

```python
MultiAgentCoordinator()
```

#### Methods

##### add_agent()

Add agent to coordinator.

```python
def add_agent(self, agent_id: str, agent: BaseAgent) -> None
```

##### execute_parallel()

Execute tasks in parallel across agents.

```python
async def execute_parallel(
    self,
    tasks: List[Dict[str, Any]]
) -> Dict[str, Any]
```

**Example:**
```python
from codex_prime.orchestration import MultiAgentCoordinator
from codex_prime.agents import CodeReviewerAgent, BugHunterAgent

coordinator = MultiAgentCoordinator()
coordinator.add_agent("reviewer", CodeReviewerAgent())
coordinator.add_agent("hunter", BugHunterAgent())

results = await coordinator.execute_parallel([
    {"agent": "reviewer", "task": "Review src/main.py"},
    {"agent": "hunter", "task": "Find bugs in src/utils.py"}
])
```

---

## Workflow Automation

### WorkflowEngine

Execute YAML/JSON workflow definitions.

```python
from codex_prime.automation import WorkflowEngine
```

#### Constructor

```python
WorkflowEngine()
```

#### Methods

##### execute_workflow()

Execute a workflow.

```python
async def execute_workflow(
    self,
    workflow_id: str,
    execution_id: Optional[str] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]
```

**Example:**
```python
from codex_prime.automation import WorkflowEngine

engine = WorkflowEngine()

result = await engine.execute_workflow(
    workflow_id="daily_report",
    context={"date": "2024-01-01"}
)
```

### CronScheduler

Schedule workflows with cron expressions.

```python
from codex_prime.automation import CronScheduler
```

#### Methods

##### add_task()

Add scheduled task.

```python
def add_task(
    self,
    task_id: str,
    name: str,
    workflow_id: str,
    cron_expression: str,
    context: Optional[Dict] = None
) -> None
```

**Example:**
```python
from codex_prime.automation import CronScheduler, WorkflowEngine

engine = WorkflowEngine()
scheduler = CronScheduler(engine)

scheduler.add_task(
    task_id="daily_report",
    name="Daily Analytics Report",
    workflow_id="analytics_report",
    cron_expression="0 9 * * *"  # 9 AM daily
)

await scheduler.start()
```

---

## Plugin System

### PluginManager

Manage plugin lifecycle.

```python
from codex_prime.plugins import PluginManager
```

#### Constructor

```python
PluginManager(
    plugins_dir: Path,
    registry_file: Path,
    auto_scan_security: bool = True
)
```

#### Methods

##### install_plugin()

Install a plugin.

```python
def install_plugin(
    self,
    source: Path,
    force: bool = False
) -> PluginManifest
```

**Example:**
```python
from pathlib import Path
from codex_prime.plugins import PluginManager

manager = PluginManager(
    plugins_dir=Path("~/.codex_prime/plugins").expanduser(),
    registry_file=Path("~/.codex_prime/registry.json").expanduser()
)

manifest = manager.install_plugin(Path("plugins/my-plugin"))
print(f"Installed: {manifest.name} v{manifest.version}")
```

##### load_plugin()

Load a plugin into memory.

```python
def load_plugin(
    self,
    plugin_id: str,
    config: Optional[Dict[str, Any]] = None
) -> PluginInstance
```

**Example:**
```python
instance = manager.load_plugin("weather-tool", config={
    "api_key": "your-key",
    "default_city": "San Francisco"
})

tool = instance.get_tool()
result = tool.execute(city="New York")
```

---

## Reasoning Modules

### ChainOfThought

Chain-of-thought reasoning.

```python
from codex_prime.reasoning import ChainOfThoughtReasoner
```

#### Methods

##### reason()

Perform chain-of-thought reasoning.

```python
def reason(
    self,
    problem: str,
    steps: Optional[int] = None
) -> Dict[str, Any]
```

**Example:**
```python
from codex_prime.reasoning import ChainOfThoughtReasoner

reasoner = ChainOfThoughtReasoner()

result = reasoner.reason(
    problem="How can I optimize database queries?"
)

for step in result['steps']:
    print(f"Step {step['number']}: {step['thought']}")
```

---

## Domain Agents

### CodeReviewerAgent

Specialized code review agent.

```python
from codex_prime.agents import CodeReviewerAgent
```

#### Constructor

```python
CodeReviewerAgent(
    config: Optional[Dict[str, Any]] = None
)
```

#### Methods

##### execute()

Review code.

```python
def execute(
    self,
    code: str,
    language: Optional[str] = None
) -> Dict[str, Any]
```

**Example:**
```python
from codex_prime.agents import CodeReviewerAgent

reviewer = CodeReviewerAgent(config={
    "strict_mode": True,
    "check_security": True
})

result = reviewer.execute("""
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}'"
    return db.execute(query)
""")

for issue in result['issues']:
    print(f"[{issue['severity']}] {issue['description']}")
```

---

## Error Handling

All APIs raise standard exceptions:

- `ValueError`: Invalid parameters
- `RuntimeError`: Execution errors
- `FileNotFoundError`: Missing files
- `PermissionError`: Access denied

**Example:**
```python
try:
    vault.add_ember("test")
except ValueError as e:
    print(f"Invalid input: {e}")
except RuntimeError as e:
    print(f"Runtime error: {e}")
```

---

## Async Support

Many methods support async execution:

```python
import asyncio
from codex_prime.automation import WorkflowEngine

async def main():
    engine = WorkflowEngine()
    result = await engine.execute_workflow("my_workflow")
    print(result)

asyncio.run(main())
```

---

For complete examples, see the [examples/](../examples/) directory.
