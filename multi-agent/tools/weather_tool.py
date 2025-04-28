from tools.base_tool import BaseTool

class WeatherTool(BaseTool):
    """
    Simulated weather lookup tool.
    """

    def name(self) -> str:
        return "weather"

    def invoke(self, input_data: dict) -> dict:
        location = input_data.get("location", "Unknown")
        # Simulate output
        return {
            "location": location,
            "forecast": "Sunny, 25°C",
            "humidity": "42%",
        }
