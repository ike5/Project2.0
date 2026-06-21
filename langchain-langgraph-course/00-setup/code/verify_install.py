"""Verify the course environment: package versions, a running Ollama server, and one live call.

Run:
    python 00-setup/code/verify_install.py

Expected: version lines, an "Ollama reachable" message, a live reply, and "live call OK".
No API key needed — this talks to your local Ollama server (http://localhost:11434).
"""

import sys
import urllib.request
from importlib.metadata import PackageNotFoundError, version

OLLAMA_URL = "http://localhost:11434/api/version"
CHAT_MODEL = "llama3.1"   # change this if you pulled a different model


def show_version(package: str) -> None:
    """Print an installed package version, or a clear NOT INSTALLED note."""
    try:
        print(f"{package:<20}: {version(package)}")
    except PackageNotFoundError:
        print(f"{package:<20}: NOT INSTALLED  (pip install -r ../requirements.txt)")


def main() -> None:
    print("=" * 52)
    print("LangChain + Ollama environment check")
    print("=" * 52)
    for pkg in ("langchain", "langgraph", "langchain-ollama"):
        show_version(pkg)

    # Ollama runs locally — confirm the server answers before we call a model.
    try:
        with urllib.request.urlopen(OLLAMA_URL, timeout=5) as resp:
            resp.read()
        print("\nOllama server       : reachable at localhost:11434 ✅")
    except Exception as e:  # noqa: BLE001
        print(f"\nOllama server NOT reachable: {e}")
        print("  Start it with:  ollama serve   (in its own terminal)")
        print("  Install from :  https://ollama.com")
        sys.exit(1)

    # One real call to confirm the model is pulled and generation works.
    print(f"\nMaking one live call to '{CHAT_MODEL}'...")
    try:
        from langchain_ollama import ChatOllama

        model = ChatOllama(model=CHAT_MODEL, num_predict=64)
        reply = model.invoke("Reply with exactly: hello from ollama")
        print(f"model says          : {reply.content}")
    except Exception as e:  # noqa: BLE001 - surface a friendly hint, not a stack trace
        print(f"\nLive call FAILED: {e}")
        print("Hints:")
        print(f"  - Model not found? Run:  ollama pull {CHAT_MODEL}")
        print("  - Server down? Run:      ollama serve")
        sys.exit(1)

    print("live call OK ✅")
    print("\nEnvironment looks good. On to Module 01!")


if __name__ == "__main__":
    main()
