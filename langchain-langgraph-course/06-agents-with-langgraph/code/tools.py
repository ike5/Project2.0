"""A few @tools reused across this module's scripts.

Run (smoke-test the tools directly, no API key needed):
    python 06-agents-with-langgraph/code/tools.py

Import them elsewhere with:
    from tools import TOOLS, multiply, get_weather, word_count
"""

from langchain_core.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city. Returns a short description."""
    # Canned data so the script runs offline and deterministically — a real
    # tool would call a weather API here.
    canned = {
        "tokyo": "18°C and rainy",
        "paris": "24°C and sunny",
        "london": "15°C and overcast",
        "new york": "21°C and partly cloudy",
    }
    return canned.get(city.strip().lower(), f"No data for {city} (try Tokyo, Paris, London).")


@tool
def word_count(text: str) -> int:
    """Count the number of whitespace-separated words in a piece of text."""
    return len(text.split())


# A ready-made list so scripts can `from tools import TOOLS`.
TOOLS = [multiply, get_weather, word_count]


if __name__ == "__main__":
    # Tools are Runnables: call them with .invoke(args_dict).
    print("multiply.invoke({'a': 23, 'b': 19}) ->", multiply.invoke({"a": 23, "b": 19}))
    print("get_weather.invoke({'city': 'Tokyo'}) ->", get_weather.invoke({"city": "Tokyo"}))
    print("word_count.invoke({'text': 'one two three'}) ->",
          word_count.invoke({"text": "one two three"}))
    print("\nTool names exposed to the model:", [t.name for t in TOOLS])
