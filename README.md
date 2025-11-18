# Codex Prime - Agent OS

A functional intelligence system with expansion modules for building AI agents with persistent memory, state management, and self-correction capabilities.

## Features

- **State Capsule**: Persistent agent identity and mission
- **Memory Vault**: Three-tier memory system (Embers, Runes, Glyphs)
- **Fortification Loop**: Self-critique and revision mechanism
- **Drift Monitor**: Detect and correct degraded output quality
- **Command DSL**: Lightweight command language for agent control
- **Provider Abstraction**: Support for multiple LLM providers

## Quick Start

```bash
# Install
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -e ".[dev]"

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python examples/run_cli.py --project demo --persona personas/codex_prime.yaml
```

## Testing

```bash
pytest -q
pytest --cov=codex_prime --cov-report=xml
```

## Architecture

See `docs/ARCHITECTURE.md` for detailed system design.

## License

MIT
