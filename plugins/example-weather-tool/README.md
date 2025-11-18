# Weather Tool Plugin

A simple weather information tool plugin for Codex Prime that demonstrates the plugin system functionality.

## Features

- Get weather information for any city
- Support for Celsius and Fahrenheit units
- Lifecycle hooks (init/shutdown)
- Configuration support

## Installation

```bash
# Install via plugin manager
codex-prime plugin install path/to/example-weather-tool

# Or install from ZIP
codex-prime plugin install example-weather-tool.zip
```

## Configuration

```yaml
api_key: "your-api-key-here"  # Optional for demo
default_city: "San Francisco"
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
manager.install_plugin("plugins/example-weather-tool")
instance = manager.load_plugin("example-weather-tool")

# Get the tool
tool = instance.get_tool()

# Use the tool
result = tool.execute(city="New York", units="fahrenheit")
print(result)
# Output: {'city': 'New York', 'temperature': 72, 'units': '°F', ...}
```

## Development

This is a demo plugin that returns mock weather data. In a production implementation, you would:

1. Integrate with a real weather API (OpenWeatherMap, WeatherAPI, etc.)
2. Add proper error handling
3. Implement caching for API responses
4. Add rate limiting

## License

MIT License - see LICENSE file for details
