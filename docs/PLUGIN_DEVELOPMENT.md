# Plugin Development Tutorial

Learn how to create plugins for Codex Prime Agent OS.

## Table of Contents

1. [Introduction](#introduction)
2. [Plugin Types](#plugin-types)
3. [Quick Start](#quick-start)
4. [Plugin Structure](#plugin-structure)
5. [Creating a Tool Plugin](#creating-a-tool-plugin)
6. [Creating a Provider Plugin](#creating-a-provider-plugin)
7. [Creating a Persona Plugin](#creating-a-persona-plugin)
8. [Testing Your Plugin](#testing-your-plugin)
9. [Publishing Your Plugin](#publishing-your-plugin)
10. [Best Practices](#best-practices)

## Introduction

Plugins extend Codex Prime's functionality without modifying core code. The plugin system supports:

- Dynamic loading/unloading
- Security scanning
- Version management
- Configuration management
- Lifecycle hooks

## Plugin Types

| Type | Purpose | Examples |
|------|---------|----------|
| **Tool** | Add new capabilities | API integrations, data processors |
| **Provider** | Add LLM providers | Custom models, local inference |
| **Memory** | Custom storage backends | Database connectors, cloud storage |
| **Command** | DSL extensions | Custom commands |
| **Persona** | Pre-configured agents | Domain experts, character templates |

## Quick Start

### 1. Choose a Plugin Template

```bash
# Copy an example plugin as template
cp -r plugins/example-weather-tool plugins/my-plugin
cd plugins/my-plugin
```

### 2. Edit the Manifest

Edit `plugin.yaml`:

```yaml
id: my-plugin
name: My Awesome Plugin
version: 1.0.0
type: tool
entry_point: plugin.py
author: Your Name
description: A plugin that does something awesome
license: MIT
keywords:
  - awesome
  - useful
dependencies: []
python_requires: ">=3.8"
hooks:
  - init
  - shutdown
```

### 3. Implement Your Plugin

Edit `plugin.py` - see type-specific sections below.

### 4. Test Locally

```python
from pathlib import Path
from codex_prime.plugins import PluginManager

manager = PluginManager(
    plugins_dir=Path("plugins"),
    registry_file=Path("test_registry.json")
)

# Install and test
manifest = manager.install_plugin(Path("plugins/my-plugin"))
instance = manager.load_plugin("my-plugin")
```

### 5. Submit to Community

Create a PR with your plugin in the `plugins/` directory.

## Plugin Structure

```
my-plugin/
├── plugin.yaml          # Manifest (required)
├── plugin.py           # Main implementation (required)
├── README.md           # Documentation (required)
├── requirements.txt    # Python dependencies (optional)
├── config_schema.json  # Configuration schema (optional)
├── tests/             # Plugin tests (recommended)
│   └── test_plugin.py
└── examples/          # Usage examples (recommended)
    └── example.py
```

## Creating a Tool Plugin

Tools add new capabilities to the agent.

### Step 1: Define the Manifest

```yaml
id: weather-api-tool
name: Weather API Tool
version: 1.0.0
type: tool
entry_point: weather.py
author: Your Name
description: Get weather information via API
license: MIT
keywords:
  - weather
  - api
dependencies:
  - name: requests
    version: ">=2.28.0"
python_requires: ">=3.8"
hooks:
  - init
  - shutdown
config_schema:
  type: object
  properties:
    api_key:
      type: string
      description: Weather API key
    default_units:
      type: string
      enum: [metric, imperial]
      default: metric
```

### Step 2: Implement the Tool

`weather.py`:

```python
"""Weather API Tool Plugin."""

from typing import Dict, Any
import requests


class WeatherApiTool:
    """Tool for fetching weather information."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize the tool with configuration.

        Args:
            config: Plugin configuration dictionary
        """
        self.api_key = config.get("api_key")
        self.default_units = config.get("default_units", "metric")

        if not self.api_key:
            raise ValueError("API key is required")

    def init(self):
        """Lifecycle hook: Called when plugin is loaded."""
        print(f"Weather API Tool initialized with {self.default_units} units")

    def shutdown(self):
        """Lifecycle hook: Called when plugin is unloaded."""
        print("Weather API Tool shutting down")

    # Required methods for Tool plugins

    def get_name(self) -> str:
        """Get tool name.

        Returns:
            Tool name as string
        """
        return "weather_api"

    def get_description(self) -> str:
        """Get tool description.

        Returns:
            Description of what the tool does
        """
        return "Get current weather and forecast for any location"

    def get_parameters(self) -> Dict[str, Any]:
        """Get parameter schema for the tool.

        Returns:
            JSON schema for tool parameters
        """
        return {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City name or coordinates"
                },
                "units": {
                    "type": "string",
                    "enum": ["metric", "imperial"],
                    "description": "Temperature units",
                    "default": self.default_units
                },
                "days": {
                    "type": "integer",
                    "description": "Number of forecast days",
                    "minimum": 1,
                    "maximum": 7,
                    "default": 1
                }
            },
            "required": ["location"]
        }

    def execute(
        self,
        location: str,
        units: str = None,
        days: int = 1
    ) -> Dict[str, Any]:
        """Execute the tool to get weather information.

        Args:
            location: City name or coordinates
            units: Temperature units (metric/imperial)
            days: Number of forecast days

        Returns:
            Weather data dictionary

        Raises:
            ValueError: If location is invalid
            RuntimeError: If API request fails
        """
        if not location:
            raise ValueError("Location is required")

        units = units or self.default_units

        # Call weather API
        url = "https://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": self.api_key,
            "q": location,
            "days": days,
            "aqi": "no"
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            # Format response
            current = data["current"]
            forecast = data["forecast"]["forecastday"]

            return {
                "location": data["location"]["name"],
                "current": {
                    "temp": current["temp_c"] if units == "metric" else current["temp_f"],
                    "condition": current["condition"]["text"],
                    "humidity": current["humidity"],
                    "wind_speed": current["wind_kph"] if units == "metric" else current["wind_mph"]
                },
                "forecast": [
                    {
                        "date": day["date"],
                        "max_temp": day["day"]["maxtemp_c"] if units == "metric" else day["day"]["maxtemp_f"],
                        "min_temp": day["day"]["mintemp_c"] if units == "metric" else day["day"]["mintemp_f"],
                        "condition": day["day"]["condition"]["text"]
                    }
                    for day in forecast
                ]
            }

        except requests.RequestException as e:
            raise RuntimeError(f"Weather API request failed: {e}")

    def __call__(self, **kwargs) -> Dict[str, Any]:
        """Make the tool callable directly.

        This is a convenience method for easier invocation.
        """
        return self.execute(**kwargs)
```

### Step 3: Write Tests

`tests/test_plugin.py`:

```python
"""Tests for Weather API Tool."""

import pytest
from weather import WeatherApiTool


class TestWeatherApiTool:
    """Test suite for Weather API Tool."""

    @pytest.fixture
    def tool(self):
        """Create tool instance for testing."""
        return WeatherApiTool(config={
            "api_key": "test_key_12345",
            "default_units": "metric"
        })

    def test_initialization(self, tool):
        """Test tool initialization."""
        assert tool.api_key == "test_key_12345"
        assert tool.default_units == "metric"

    def test_get_name(self, tool):
        """Test get_name method."""
        assert tool.get_name() == "weather_api"

    def test_get_description(self, tool):
        """Test get_description method."""
        description = tool.get_description()
        assert "weather" in description.lower()

    def test_parameter_schema(self, tool):
        """Test parameter schema."""
        schema = tool.get_parameters()
        assert schema["type"] == "object"
        assert "location" in schema["properties"]
        assert "location" in schema["required"]

    def test_execute_requires_location(self, tool):
        """Test that location is required."""
        with pytest.raises(ValueError, match="Location is required"):
            tool.execute(location="")

    @pytest.mark.integration
    def test_execute_real_api(self, tool):
        """Test with real API (requires valid key)."""
        # Skip if no real API key
        if tool.api_key == "test_key_12345":
            pytest.skip("No real API key provided")

        result = tool.execute(location="London")
        assert "location" in result
        assert "current" in result
        assert result["location"] == "London"
```

### Step 4: Write Documentation

`README.md`:

```markdown
# Weather API Tool

Get current weather and forecasts for any location.

## Features

- Current weather conditions
- Multi-day forecasts (up to 7 days)
- Support for metric and imperial units
- Location search by city name or coordinates

## Installation

```bash
codex-prime plugin install weather-api-tool
```

## Configuration

```yaml
api_key: "your-api-key-here"
default_units: "metric"  # or "imperial"
```

Get a free API key from [WeatherAPI.com](https://www.weatherapi.com/)

## Usage

```python
from codex_prime.plugins import PluginManager

manager = PluginManager()
instance = manager.load_plugin("weather-api-tool", config={
    "api_key": "your-key",
    "default_units": "metric"
})

tool = instance.get_tool()
result = tool.execute(location="New York", days=3)
print(result)
```

## Example Output

```json
{
  "location": "New York",
  "current": {
    "temp": 22,
    "condition": "Partly cloudy",
    "humidity": 65,
    "wind_speed": 15
  },
  "forecast": [...]
}
```

## License

MIT
```

## Creating a Provider Plugin

Provider plugins add new LLM backends.

### Implementation Example

`provider.py`:

```python
"""Custom LLM Provider Plugin."""

from typing import List, Dict, Any, Optional, Iterator
from codex_prime.providers.base import BaseProvider


class CustomLLMProvider(BaseProvider):
    """Custom LLM provider implementation."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize provider.

        Args:
            config: Provider configuration
        """
        super().__init__(config)
        self.api_key = config.get("api_key")
        self.base_url = config.get("base_url", "https://api.custom.com")
        self.model = config.get("model", "custom-model-v1")

    def chat(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> str:
        """Generate chat completion.

        Args:
            messages: List of chat messages
            **kwargs: Additional parameters

        Returns:
            Generated response text
        """
        # Implement your API call here
        # ...
        return response_text

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        **kwargs
    ) -> Iterator[str]:
        """Stream chat completion.

        Args:
            messages: List of chat messages
            **kwargs: Additional parameters

        Yields:
            Response text chunks
        """
        # Implement streaming here
        # ...
        yield chunk

    def get_embedding(self, text: str) -> List[float]:
        """Get text embedding.

        Args:
            text: Text to embed

        Returns:
            Embedding vector
        """
        # Implement embedding generation
        # ...
        return embedding_vector
```

## Creating a Persona Plugin

Persona plugins provide pre-configured agent personalities.

### Implementation Example

`persona.py`:

```python
"""Domain Expert Persona Plugin."""

from typing import Dict, Any


class DataScientistPersona:
    """Data scientist persona with expertise in ML/AI."""

    def __init__(self, config: Dict[str, Any]):
        """Initialize persona."""
        self.experience_level = config.get("experience_level", "senior")
        self.specialization = config.get("specialization", "machine learning")

    def get_system_prompt(self) -> str:
        """Get system prompt for this persona."""
        return f"""You are a {self.experience_level} data scientist specializing in {self.specialization}.

Your expertise includes:
- Machine learning and deep learning
- Statistical analysis and hypothesis testing
- Data visualization and storytelling
- Python (pandas, scikit-learn, TensorFlow, PyTorch)
- SQL and database optimization
- Feature engineering and model selection

Your approach:
1. Ask clarifying questions about the data and business problem
2. Suggest appropriate techniques and methodologies
3. Explain concepts clearly with examples
4. Consider trade-offs between accuracy, interpretability, and performance
5. Recommend best practices for production ML systems

Always be thorough but concise, and back up recommendations with reasoning."""

    def get_persona_config(self) -> Dict[str, Any]:
        """Get complete persona configuration."""
        return {
            "name": f"{self.experience_level.title()} Data Scientist",
            "role": "data_scientist",
            "specialties": [self.specialization, "python", "statistics"],
            "system_prompt": self.get_system_prompt(),
            "temperature": 0.7,
            "max_tokens": 2000
        }

    def get_example_prompts(self) -> list:
        """Get example prompts for this persona."""
        return [
            "How should I approach feature engineering for time series data?",
            "What model should I use for customer churn prediction?",
            "Explain gradient boosting in simple terms",
            "How can I handle imbalanced datasets?",
            "What metrics should I use for multi-class classification?"
        ]
```

## Testing Your Plugin

### Unit Tests

```python
import pytest
from my_plugin import MyPlugin


def test_plugin_initialization():
    """Test plugin initializes correctly."""
    plugin = MyPlugin(config={"key": "value"})
    assert plugin.config["key"] == "value"


def test_plugin_execution():
    """Test plugin executes correctly."""
    plugin = MyPlugin(config={})
    result = plugin.execute(param="test")
    assert result is not None
```

### Integration Tests

```python
from pathlib import Path
from codex_prime.plugins import PluginManager


def test_plugin_installation():
    """Test plugin can be installed."""
    manager = PluginManager(
        plugins_dir=Path("test_plugins"),
        registry_file=Path("test_registry.json")
    )

    manifest = manager.install_plugin(Path("plugins/my-plugin"))
    assert manifest.id == "my-plugin"


def test_plugin_loading():
    """Test plugin can be loaded and used."""
    manager = PluginManager(...)
    instance = manager.load_plugin("my-plugin")

    tool = instance.get_tool()
    result = tool.execute(param="test")
    assert result is not None
```

### Security Testing

```python
from codex_prime.plugins import SecurityScanner


def test_plugin_security():
    """Test plugin passes security scan."""
    scanner = SecurityScanner()
    issues = scanner.scan_plugin(Path("plugins/my-plugin"))

    # Check for critical issues
    critical = [i for i in issues if i.severity == "critical"]
    assert len(critical) == 0, f"Critical security issues found: {critical}"
```

## Publishing Your Plugin

### 1. Prepare for Release

- [ ] All tests pass
- [ ] Documentation complete
- [ ] Security scan passes
- [ ] README includes examples
- [ ] Version number updated
- [ ] Dependencies listed

### 2. Create Distribution

```bash
# Create ZIP distribution
cd plugins
zip -r my-plugin-1.0.0.zip my-plugin/

# Or create tar.gz
tar -czf my-plugin-1.0.0.tar.gz my-plugin/
```

### 3. Submit to Community

Create a Pull Request with:
- Plugin files in `plugins/my-plugin/`
- Update to `plugins/README.md` listing your plugin
- Issue using the Plugin Submission template

### 4. Marketplace Listing

Once approved, your plugin will be:
- Listed in the community marketplace
- Available via `codex-prime plugin search`
- Installable via `codex-prime plugin install`

## Best Practices

### Security

1. **Never hardcode secrets**
   ```python
   # Bad
   API_KEY = "sk-1234567890"

   # Good
   api_key = config.get("api_key")
   ```

2. **Validate all inputs**
   ```python
   def execute(self, user_input: str):
       if not user_input or len(user_input) > 1000:
           raise ValueError("Invalid input")
   ```

3. **Use timeouts for external calls**
   ```python
   response = requests.get(url, timeout=10)
   ```

### Performance

1. **Cache expensive operations**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def expensive_operation(param):
       # ...
   ```

2. **Use async for I/O operations**
   ```python
   async def fetch_data(self, url):
       async with aiohttp.ClientSession() as session:
           async with session.get(url) as response:
               return await response.json()
   ```

### Maintainability

1. **Follow Python conventions**
   - PEP 8 style guide
   - Type hints for all functions
   - Comprehensive docstrings

2. **Handle errors gracefully**
   ```python
   try:
       result = risky_operation()
   except SpecificError as e:
       logger.error(f"Operation failed: {e}")
       return fallback_value
   ```

3. **Log important events**
   ```python
   import logging

   logger = logging.getLogger(__name__)
   logger.info("Processing request", extra={"param": value})
   ```

### Documentation

1. **Clear README with examples**
2. **API documentation in docstrings**
3. **Configuration examples**
4. **Troubleshooting section**

## Common Issues

### Issue: Plugin not loading

**Solution**: Check manifest validation
```python
from codex_prime.plugins import PluginManifest

manifest = PluginManifest.from_yaml(Path("plugin.yaml"))
# Will raise ValueError if invalid
```

### Issue: Import errors

**Solution**: Ensure dependencies in requirements.txt
```txt
requests>=2.28.0
aiohttp>=3.8.0
```

### Issue: Security scan fails

**Solution**: Review and fix flagged code
```python
# Avoid using eval, exec, os.system
# Use safer alternatives
```

## Resources

- [Plugin Examples](../plugins/)
- [API Reference](API_REFERENCE.md)
- [Contributing Guide](../CONTRIBUTING.md)
- [Community Forum](https://github.com/yourusername/agent-OS/discussions)

## Support

- GitHub Discussions for questions
- GitHub Issues for bugs
- Plugin Submission template for new plugins

---

Happy plugin development! 🚀
