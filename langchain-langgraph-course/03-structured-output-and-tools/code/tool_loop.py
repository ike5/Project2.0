"""The full manual tool-calling loop, by hand.

Run:
    python 03-structured-output-and-tools/code/tool_loop.py

Needs a running local Ollama server (ollama serve). Flow: ask -> model requests a tool -> WE run it ->
feed the result back as a ToolMessage -> model writes the final answer.

This is the hand-rolled version of what Module 06 automates with a LangGraph
ToolNode + a conditional edge. Doing it manually shows what each node does.
"""

from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool


@tool
def multiply(a: int, b: int) -> int:
    """Multiply two integers and return the product."""
    return a * b


# Look up tools by name so we can dispatch whatever the model requests.
TOOLS = [multiply]
TOOLS_BY_NAME = {t.name: t for t in TOOLS}


def main() -> None:
    model = ChatOllama(model="llama3.1", num_predict=1024)
    model_with_tools = model.bind_tools(TOOLS)

    messages = [HumanMessage("What is 12 * 7?")]

    # Step 1: the model decides it needs a tool and REQUESTS it (does not run it).
    ai = model_with_tools.invoke(messages)
    messages.append(ai)  # keep the request in the conversation history
    print("Model's tool requests:", ai.tool_calls)

    if not ai.tool_calls:
        # Defensive: if the model just answered, we're already done.
        print("\nNo tool requested. Final answer:", ai.content)
        return

    # Step 2: WE run each requested tool and feed the result back as a ToolMessage.
    for call in ai.tool_calls:  # may be more than one tool call
        the_tool = TOOLS_BY_NAME[call["name"]]
        result = the_tool.invoke(call["args"])  # e.g. multiply.invoke({'a': 12, 'b': 7})
        print(f"  ran {call['name']}({call['args']}) -> {result}")
        messages.append(
            ToolMessage(content=str(result), tool_call_id=call["id"])  # pair by id!
        )

    # Step 3: the model reads the ToolMessage(s) and writes the natural-language answer.
    final = model_with_tools.invoke(messages)
    print("\nFinal answer:", final.content)
    print("\n(Module 06 replaces this whole loop with a LangGraph ToolNode.)")


if __name__ == "__main__":
    main()
