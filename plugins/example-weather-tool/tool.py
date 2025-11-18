"""Example weather tool plugin."""

from typing import Dict, Any
import random


class WeatherTool:
    """A simple weather tool that demonstrates plugin functionality.

    In a real implementation, this would connect to a weather API.
    This is a demo that returns mock data.
    """

    def __init__(self, config: Dict[str, Any]):
        """Initialize the weather tool."""
        self.api_key = config.get("api_key")
        self.default_city = config.get("default_city", "San Francisco")
        print(f"Weather Tool initialized with default city: {self.default_city}")

    def init(self):
        """Lifecycle hook: initialization."""
        print("Weather Tool: init hook called")

    def shutdown(self):
        """Lifecycle hook: shutdown."""
        print("Weather Tool: shutdown hook called")

    def get_name(self) -> str:
        """Get tool name."""
        return "weather"

    def get_description(self) -> str:
        """Get tool description."""
        return "Get current weather information for a city"

    def get_parameters(self) -> Dict[str, Any]:
        """Get tool parameters schema."""
        return {
            "type": "object",
            "properties": {
                "city": {
                    "type": "string",
                    "description": "City name to get weather for"
                },
                "units": {
                    "type": "string",
                    "enum": ["celsius", "fahrenheit"],
                    "description": "Temperature units",
                    "default": "celsius"
                }
            },
            "required": ["city"]
        }

    def execute(self, city: str, units: str = "celsius") -> Dict[str, Any]:
        """Execute the weather tool.

        Args:
            city: City name
            units: Temperature units (celsius or fahrenheit)

        Returns:
            Weather data dictionary
        """
        # Mock weather data
        conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear"]
        temp_c = random.randint(10, 30)

        if units == "fahrenheit":
            temp = (temp_c * 9/5) + 32
            units_symbol = "°F"
        else:
            temp = temp_c
            units_symbol = "°C"

        return {
            "city": city,
            "temperature": temp,
            "units": units_symbol,
            "condition": random.choice(conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(5, 25),
            "description": f"The weather in {city} is {random.choice(conditions).lower()} "
                          f"with a temperature of {temp}{units_symbol}."
        }

    def __call__(self, **kwargs) -> Dict[str, Any]:
        """Make the tool callable."""
        return self.execute(**kwargs)
