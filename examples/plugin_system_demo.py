"""Demonstration of the Codex Prime plugin system.

This example shows how to:
1. Initialize the plugin manager
2. Install plugins
3. Load and use plugins
4. Scan plugins for security issues
5. Manage plugin lifecycle
"""

from pathlib import Path
from codex_prime.plugins import (
    PluginManager,
    PluginType,
    SecurityScanner
)


def main():
    """Run plugin system demonstration."""
    print("=" * 60)
    print("Codex Prime Plugin System Demo")
    print("=" * 60)
    print()

    # Initialize plugin manager
    plugins_dir = Path.home() / ".codex_prime" / "plugins"
    registry_file = Path.home() / ".codex_prime" / "plugin_registry.json"

    manager = PluginManager(
        plugins_dir=plugins_dir,
        registry_file=registry_file,
        auto_scan_security=True
    )

    print(f"Plugin directory: {plugins_dir}")
    print(f"Registry file: {registry_file}")
    print()

    # Example 1: Install weather tool plugin
    print("1. Installing Weather Tool Plugin")
    print("-" * 40)

    try:
        weather_plugin_path = Path(__file__).parent.parent / "plugins" / "example-weather-tool"

        if weather_plugin_path.exists():
            manifest = manager.install_plugin(weather_plugin_path)
            print(f"✓ Installed: {manifest.name} v{manifest.version}")
            print(f"  Type: {manifest.type.value}")
            print(f"  Author: {manifest.author}")
            print(f"  Description: {manifest.description}")
        else:
            print(f"✗ Plugin not found at {weather_plugin_path}")

    except Exception as e:
        print(f"✗ Error installing plugin: {e}")

    print()

    # Example 2: Install persona plugin
    print("2. Installing Creative Writer Persona Plugin")
    print("-" * 40)

    try:
        persona_plugin_path = Path(__file__).parent.parent / "plugins" / "example-persona"

        if persona_plugin_path.exists():
            manifest = manager.install_plugin(persona_plugin_path)
            print(f"✓ Installed: {manifest.name} v{manifest.version}")
            print(f"  Type: {manifest.type.value}")
        else:
            print(f"✗ Plugin not found at {persona_plugin_path}")

    except Exception as e:
        print(f"✗ Error installing plugin: {e}")

    print()

    # Example 3: List installed plugins
    print("3. Listing Installed Plugins")
    print("-" * 40)

    plugins = manager.list_plugins()
    print(f"Total plugins: {len(plugins)}")

    for plugin in plugins:
        status = "✓ Loaded" if plugin["loaded"] else "○ Not loaded"
        enabled = "✓" if plugin["enabled"] else "✗"
        print(f"  [{enabled}] {plugin['name']} v{plugin['version']}")
        print(f"      {status} | Type: {plugin['type']} | Usage: {plugin['usage_count']}")

    print()

    # Example 4: Load and use weather tool
    print("4. Loading and Using Weather Tool")
    print("-" * 40)

    try:
        instance = manager.load_plugin("example-weather-tool", config={
            "default_city": "San Francisco"
        })

        tool = instance.get_tool()
        print(f"✓ Loaded tool: {tool.get_name()}")
        print(f"  Description: {tool.get_description()}")

        # Use the tool
        result = tool.execute(city="New York", units="fahrenheit")
        print(f"\nWeather in {result['city']}:")
        print(f"  Temperature: {result['temperature']}{result['units']}")
        print(f"  Condition: {result['condition']}")
        print(f"  Humidity: {result['humidity']}%")
        print(f"  Wind Speed: {result['wind_speed']} mph")

    except Exception as e:
        print(f"✗ Error: {e}")

    print()

    # Example 5: Load and use persona
    print("5. Loading and Using Persona Plugin")
    print("-" * 40)

    try:
        instance = manager.load_plugin("example-persona", config={
            "writing_style": "poetic",
            "tone": "humorous"
        })

        persona = instance.get_persona()
        metadata = persona.get_metadata()

        print(f"✓ Loaded persona: {metadata['name']}")
        print(f"  Writing style: {metadata['writing_style']}")
        print(f"  Tone: {metadata['tone']}")
        print(f"\nExample prompts:")

        for i, prompt in enumerate(metadata['example_prompts'][:3], 1):
            print(f"  {i}. {prompt}")

    except Exception as e:
        print(f"✗ Error: {e}")

    print()

    # Example 6: Security scanning
    print("6. Security Scanning")
    print("-" * 40)

    scanner = SecurityScanner()
    weather_plugin_path = plugins_dir / "example-weather-tool"

    if weather_plugin_path.exists():
        issues = scanner.scan_plugin(weather_plugin_path)
        summary = scanner.get_summary()

        print(f"Scanned: example-weather-tool")
        print(f"  Total issues: {summary['total_issues']}")
        print(f"  Critical: {summary['by_severity']['critical']}")
        print(f"  High: {summary['by_severity']['high']}")
        print(f"  Medium: {summary['by_severity']['medium']}")
        print(f"  Low: {summary['by_severity']['low']}")

        if scanner.is_safe():
            print("  ✓ Plugin is safe to use")
        else:
            print("  ✗ Plugin has security concerns")

    print()

    # Example 7: Plugin statistics
    print("7. Plugin System Statistics")
    print("-" * 40)

    stats = manager.get_stats()
    print(f"Total plugins: {stats['total_plugins']}")
    print(f"Enabled: {stats['enabled_plugins']}")
    print(f"Disabled: {stats['disabled_plugins']}")
    print(f"Loaded in memory: {stats['loaded_plugins']}")
    print(f"Total usage: {stats['total_usage']}")
    print(f"\nBy type:")

    for plugin_type, count in stats['by_type'].items():
        print(f"  {plugin_type}: {count}")

    print()

    # Example 8: Search plugins
    print("8. Searching Plugins")
    print("-" * 40)

    results = manager.search_plugins("weather")
    print(f"Search results for 'weather': {len(results)} found")

    for result in results:
        print(f"  • {result['name']} v{result['version']}")
        print(f"    {result['description']}")

    print()

    # Example 9: Unload plugin
    print("9. Unloading Plugin")
    print("-" * 40)

    try:
        manager.unload_plugin("example-weather-tool")
        print("✓ Unloaded: example-weather-tool")
    except Exception as e:
        print(f"✗ Error: {e}")

    print()

    # Example 10: Get detailed plugin info
    print("10. Detailed Plugin Information")
    print("-" * 40)

    try:
        info = manager.get_plugin_info("example-persona")
        print(f"Plugin: {info['manifest']['name']}")
        print(f"Version: {info['manifest']['version']}")
        print(f"Author: {info['manifest']['author']}")
        print(f"Type: {info['manifest']['type']}")
        print(f"Enabled: {info['enabled']}")
        print(f"Loaded: {info['loaded']}")
        print(f"Installed: {info['installed_at']}")
        print(f"Usage count: {info['usage_count']}")
        print(f"Rating: {info['rating'] or 'No ratings yet'}")

        if info['manifest']['keywords']:
            print(f"Keywords: {', '.join(info['manifest']['keywords'])}")

    except Exception as e:
        print(f"✗ Error: {e}")

    print()
    print("=" * 60)
    print("Demo completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
