# Creative Writer Persona Plugin

A creative writer persona plugin for Codex Prime that provides storytelling and content creation capabilities.

## Features

- Configurable writing styles (descriptive, concise, poetic, technical)
- Adjustable tone (formal, casual, humorous, serious)
- Pre-built system prompts for creative writing
- Example prompts and use cases

## Installation

```bash
# Install via plugin manager
codex-prime plugin install path/to/example-persona
```

## Configuration

```yaml
writing_style: "descriptive"  # or "concise", "poetic", "technical"
tone: "casual"  # or "formal", "humorous", "serious"
```

## Usage

```python
from codex_prime.plugins import PluginManager

# Initialize plugin manager
manager = PluginManager(
    plugins_dir="~/.codex_prime/plugins",
    registry_file="~/.codex_prime/plugin_registry.json"
)

# Install and load plugin
manager.install_plugin("plugins/example-persona")
instance = manager.load_plugin("example-persona", config={
    "writing_style": "poetic",
    "tone": "humorous"
})

# Get persona configuration
persona = instance.get_persona()
config = persona.get_persona_config()

print(config["system_prompt"])
print(config["example_prompts"])
```

## Customization

You can create your own persona plugins by:

1. Defining a persona class with `get_system_prompt()` method
2. Implementing configuration options
3. Providing example prompts
4. Creating a plugin.yaml manifest

## License

MIT License - see LICENSE file for details
