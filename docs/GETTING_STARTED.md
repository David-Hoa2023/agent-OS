# Getting Started with Codex Prime Agent OS

This guide will help you get up and running with Codex Prime in under 15 minutes.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Basic Configuration](#basic-configuration)
4. [First Steps](#first-steps)
5. [Common Use Cases](#common-use-cases)
6. [Troubleshooting](#troubleshooting)
7. [Next Steps](#next-steps)

## Prerequisites

### Required

- **Python 3.8 or higher** ([Download](https://www.python.org/downloads/))
- **pip** (comes with Python)
- **Git** ([Download](https://git-scm.com/downloads))

### Recommended

- **Node.js 18+** (for Web UI) - [Download](https://nodejs.org/)
- **Docker & Docker Compose** (for containerized deployment) - [Download](https://www.docker.com/get-started)

### API Keys

You'll need at least one LLM provider API key:

- **OpenAI API Key** - [Get one here](https://platform.openai.com/api-keys)
- **Anthropic API Key** (optional) - [Get one here](https://console.anthropic.com/)
- **Local Ollama** (optional, free) - [Install here](https://ollama.ai/)

## Installation

### Option 1: Standard Installation (Recommended for Development)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/agent-OS.git
cd agent-OS

# 2. Create a virtual environment
python -m venv .venv

# 3. Activate the virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
.venv\Scripts\activate

# 4. Install dependencies
pip install -e ".[dev]"

# 5. Install optional features
pip install chromadb cryptography websockets

# 6. Verify installation
python -c "import codex_prime; print('✓ Codex Prime installed successfully!')"
```

### Option 2: Docker Installation (Recommended for Production)

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/agent-OS.git
cd agent-OS

# 2. Build Docker image
docker build -t codex-prime:latest .

# 3. Run with Docker Compose (includes all services)
docker-compose up -d

# 4. Check status
docker-compose ps
```

## Basic Configuration

### 1. Environment Variables

Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit with your favorite editor
nano .env  # or vim, code, etc.
```

Add your API keys:

```env
# Required: At least one LLM provider
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Optional: Advanced features
DATABASE_URL=postgresql://user:pass@localhost:5432/codexprime
REDIS_URL=redis://localhost:6379/0
CHROMADB_URL=http://localhost:8002

# Optional: Configuration
LOG_LEVEL=INFO
CODEX_PRIME_HOME=~/.codex_prime
```

### 2. Initialize Workspace

```bash
# Create workspace directory
mkdir -p ~/.codex_prime/workspace
mkdir -p ~/.codex_prime/plugins
mkdir -p ~/.codex_prime/logs

# Initialize configuration
python -m codex_prime.cli init --workspace ~/.codex_prime/workspace
```

## First Steps

### 1. Hello World - Your First Agent

Create a file `my_first_agent.py`:

```python
from pathlib import Path
from codex_prime import AgentOS

# Initialize the agent
agent = AgentOS(
    project_name="hello_world",
    workspace=Path("~/.codex_prime/workspace").expanduser(),
    persona_path=Path("personas/codex_prime.yaml")
)

# Execute a simple task
response = agent.execute("Hello! Tell me a fun fact about Python programming.")

print(response)
```

Run it:

```bash
python my_first_agent.py
```

### 2. Using Memory

```python
from pathlib import Path
from codex_prime.memory import EnhancedMemoryVault

# Create a memory vault
vault = EnhancedMemoryVault(
    storage_path=Path("~/.codex_prime/demo_vault").expanduser(),
    use_vector_search=True
)

# Add some memories
vault.add_rune("Python was created by Guido van Rossum", tags=["python", "history"])
vault.add_rune("FastAPI is a modern web framework", tags=["python", "web"])
vault.add_rune("NumPy is used for numerical computing", tags=["python", "data"])

# Search semantically
results = vault.recall("Who created Python?", k=3)
for result in results:
    print(f"[{result['score']:.2f}] {result['text']}")
```

### 3. Using Tools

```python
from codex_prime.tools import ToolRegistry, ToolExecutor
from codex_prime.tools.builtin import create_default_toolset

# Create registry with built-in tools
registry = ToolRegistry()
for tool in create_default_toolset():
    registry.register(tool)

# Create executor
executor = ToolExecutor(registry)

# Execute Python code
result = executor.execute("execute_python", {
    "code": "import math\nprint(f'Pi is approximately {math.pi:.2f}')"
})
print(result['stdout'])

# Read a file
result = executor.execute("read_file", {
    "path": "README.md"
})
print(result['content'][:100] + "...")
```

### 4. Run the Web UI

```bash
# Terminal 1: Start backend API
python -m codex_prime.interfaces.http_server --host 0.0.0.0 --port 8000

# Terminal 2: Start frontend
cd web-ui
npm install
npm start

# Open browser to http://localhost:3000
```

### 5. Run the CLI

```bash
# Interactive CLI
python examples/run_cli.py --project demo --persona personas/codex_prime.yaml

# Or use the command
codex-prime chat --project demo
```

## Common Use Cases

### Use Case 1: Code Review Agent

```python
from codex_prime.agents import CodeReviewerAgent

# Create code reviewer
reviewer = CodeReviewerAgent(config={
    "strict_mode": True,
    "check_security": True
})

# Review code
result = reviewer.execute("""
def login(username, password):
    query = f"SELECT * FROM users WHERE username='{username}' AND password='{password}'"
    return db.execute(query)
""")

print(result['issues'])
```

### Use Case 2: Automated Workflow

Create `workflows/morning_report.yaml`:

```yaml
workflow_id: morning_report
name: Morning Intelligence Report
schedule: "0 8 * * *"  # 8 AM daily

steps:
  - step_id: fetch_news
    type: http
    config:
      url: "https://newsapi.org/v2/top-headlines"
      method: GET

  - step_id: summarize
    type: agent
    depends_on: [fetch_news]
    config:
      agent_name: summarizer
      task: "Summarize the top news stories"

  - step_id: send_email
    type: tool
    depends_on: [summarize]
    config:
      tool_name: send_email
      parameters:
        to: "me@example.com"
        subject: "Morning Intelligence Report"
```

Run it:

```python
from codex_prime.automation import WorkflowEngine, CronScheduler

engine = WorkflowEngine()
scheduler = CronScheduler(engine)

scheduler.add_task_from_file("workflows/morning_report.yaml")
await scheduler.start()
```

### Use Case 3: Multi-Agent Collaboration

```python
from codex_prime.orchestration import MultiAgentCoordinator
from codex_prime.agents import CodeReviewerAgent, BugHunterAgent

# Create agents
coordinator = MultiAgentCoordinator()
coordinator.add_agent("reviewer", CodeReviewerAgent())
coordinator.add_agent("hunter", BugHunterAgent())

# Execute in parallel
results = await coordinator.execute_parallel([
    {"agent": "reviewer", "task": "Review src/main.py for best practices"},
    {"agent": "hunter", "task": "Find bugs in src/utils.py"}
])

for agent_id, result in results.items():
    print(f"\n{agent_id}: {result}")
```

### Use Case 4: Plugin Development

Create a custom weather tool plugin:

```bash
mkdir -p plugins/my-weather-tool
cd plugins/my-weather-tool
```

Create `plugin.yaml`:

```yaml
id: my-weather-tool
name: Weather Tool
version: 1.0.0
type: tool
entry_point: tool.py
author: Your Name
description: Get weather information
```

Create `tool.py`:

```python
class WeatherTool:
    def __init__(self, config):
        self.api_key = config.get("api_key")

    def get_name(self):
        return "weather"

    def execute(self, city: str):
        # Your implementation here
        return {"temperature": 72, "condition": "Sunny"}
```

Install and use:

```python
from codex_prime.plugins import PluginManager

manager = PluginManager(
    plugins_dir="~/.codex_prime/plugins",
    registry_file="~/.codex_prime/registry.json"
)

manager.install_plugin("plugins/my-weather-tool")
instance = manager.load_plugin("my-weather-tool")
tool = instance.get_tool()

result = tool.execute(city="San Francisco")
print(result)
```

## Troubleshooting

### Common Issues

#### 1. Import Errors

```bash
# Error: ModuleNotFoundError: No module named 'codex_prime'
# Solution: Make sure you installed in editable mode and activated venv
pip install -e .
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
```

#### 2. API Key Issues

```bash
# Error: OpenAI API key not found
# Solution: Check your .env file and make sure it's loaded
export OPENAI_API_KEY=sk-your-key-here  # Temporary fix
# Or update .env and restart
```

#### 3. ChromaDB Errors

```bash
# Error: ChromaDB not installed
# Solution: Install optional dependencies
pip install chromadb
```

#### 4. Permission Errors

```bash
# Error: Permission denied when writing to ~/.codex_prime
# Solution: Create directory with proper permissions
mkdir -p ~/.codex_prime
chmod 755 ~/.codex_prime
```

#### 5. Docker Issues

```bash
# Error: Port 8000 already in use
# Solution: Stop existing service or change port
docker-compose down
# Or modify docker-compose.yml to use different port
```

### Getting Help

- **Documentation**: Check `/docs` directory
- **Examples**: See `/examples` directory for working code
- **Issues**: [GitHub Issues](https://github.com/yourusername/agent-OS/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/agent-OS/discussions)

## Next Steps

Now that you have Codex Prime running, explore these topics:

1. **Advanced Memory Management** - Learn about vector search and memory tiers
   - See [Memory Guide](MEMORY_GUIDE.md)

2. **Multi-Agent Orchestration** - Build complex agent workflows
   - See [Multi-Agent Guide](MULTI_AGENT_GUIDE.md)

3. **Plugin Development** - Extend Codex Prime with custom plugins
   - See [Plugin Development Guide](PLUGIN_DEVELOPMENT.md)

4. **Production Deployment** - Deploy to production environments
   - See [Deployment Guide](DEPLOYMENT.md)

5. **Security & Compliance** - Configure RBAC, encryption, and audit logging
   - See [Security Guide](SECURITY.md)

6. **Advanced Reasoning** - Use Chain-of-Thought and Tree of Thoughts
   - See [Reasoning Guide](REASONING_GUIDE.md)

7. **Web UI Customization** - Customize the React frontend
   - See [Web UI Guide](WEB_UI_GUIDE.md)

## Additional Resources

- [API Reference](API.md) - Complete API documentation
- [Architecture Guide](ARCHITECTURE.md) - System design and patterns
- [Implementation Status](../IMPLEMENTATION_STATUS.md) - Feature completion status
- [Expansion Roadmap](../EXPANSION_ROADMAP.md) - Phase details
- [Use Case Matrix](../USE_CASE_MATRIX.md) - Real-world applications

---

**Welcome to Codex Prime!** 🚀

You're now ready to build powerful autonomous agents. Happy coding!
