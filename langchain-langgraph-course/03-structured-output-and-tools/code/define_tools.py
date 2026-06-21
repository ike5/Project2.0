"""Define tools, bind them, and read what the model REQUESTS via .tool_calls.

Run:
    python 03-structured-output-and-tools/code/define_tools.py

Needs a running local Ollama server (ollama serve). Key lesson printed here: binding tools and asking a
question gives you a *request* to run a tool (a dict in .tool_calls) — the tool
is NOT executed. And when the question needs no tool, .tool_calls is empty.
"""

from langchain_ollama import ChatOllama
from langchain_core.tools import tool


@tool
def add(a: int, b: int) -> int:
    """Add two integers and return the sum."""
    return a + b


@tool
def get_weather(city: str) -> str:
    """Get the current weather for a given city."""
    # Canned (fake) data — a real tool would call an API here.
    return f"It's 72°F and sunny in {city}."


def section(title: str) -> None:
    print("\n" + "-" * 60)
    print(title)
    print("-" * 60)


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)
    model_with_tools = model.bind_tools([add, get_weather])

    section("1. A math question -> the model requests `add`")
    resp = model_with_tools.invoke("What is 2 + 3?")
    print(".content :", repr(resp.content), "(often empty — it's asking, not answering)")
    print(".tool_calls:", resp.tool_calls)
    for call in resp.tool_calls:
        print(f"   wants to run {call['name']}({call['args']})  id={call['id']}")
    print(">> Note: nothing ran. tool_calls is a REQUEST, not a result.")

    section("2. A weather question -> the model requests `get_weather`")
    resp2 = model_with_tools.invoke("What's the weather in Tokyo?")
    print(".tool_calls:", resp2.tool_calls)

    section("3. Chit-chat -> NO tool needed -> .tool_calls is empty")
    resp3 = model_with_tools.invoke("Say hello in one short sentence.")
    print(".tool_calls:", resp3.tool_calls, "(empty list)")
    print(".content :", repr(resp3.content))

    section("4. You can run a @tool directly with .invoke(args_dict)")
    print("add.invoke({'a': 2, 'b': 3}) =", add.invoke({"a": 2, "b": 3}))
    print("get_weather.invoke({'city': 'Paris'}) =", get_weather.invoke({"city": "Paris"}))

    print("\nDone. Always branch on `if resp.tool_calls:` — never assume a tool ran.")


if __name__ == "__main__":
    main()
