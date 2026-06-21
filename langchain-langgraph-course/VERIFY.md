# VERIFY — confirm your environment works

Run these before Module 01. Each has an expected result. If one fails, the fix is noted.
This course runs **locally with Ollama** — there are no API keys to set.

---

## 1. Python is 3.10+

```bash
python --version
```
✅ `Python 3.10.x` or newer. If `python` is missing, try `python3` (and use `python3`
throughout the course). LangGraph requires 3.10+.

## 2. A clean virtual environment (recommended)

```bash
cd langchain-langgraph-course
python -m venv .venv
source .venv/bin/activate           # Windows PowerShell: .venv\Scripts\Activate.ps1
```
✅ Your prompt shows `(.venv)`. Everything below installs *into* this sandbox, leaving your
system Python untouched.

## 3. Install the Python stack

```bash
pip install -r requirements.txt
```
✅ Finishes without red errors.

## 4. Ollama is installed and running

Install Ollama from <https://ollama.com> if you haven't. Then:

```bash
ollama --version
curl -s http://localhost:11434/api/version
```
✅ Both print a version. If the `curl` fails with "connection refused", start the server:

```bash
ollama serve            # leave it running in its own terminal (often already running)
```

## 5. Pull the two models this course uses

```bash
ollama pull llama3.1            # the chat model (~4.7 GB; one-time download)
ollama pull nomic-embed-text    # the embedding model for Module 04 (~270 MB)
ollama list                     # should show both
```
✅ `ollama list` lists `llama3.1` and `nomic-embed-text`. (Short on disk or RAM? You can
swap `llama3.1` for `llama3.2` everywhere — edit the `model=` argument — but tool-calling in
Modules 03/06/07 is more reliable on `llama3.1`.)

## 6. Imports resolve

```bash
python -c "import langchain, langgraph; from langchain_ollama import ChatOllama, OllamaEmbeddings; print('imports OK ✅')"
```
✅ Prints `imports OK ✅`. An `ImportError` means step 3 didn't finish — re-run it inside the
activated venv.

## 7. A live local model call works (the real test)

```bash
python 00-setup/code/verify_install.py
```
✅ Prints the installed versions, then a one-line reply from your local Llama model, then
`live call OK ✅`.

Common failures:
- `ConnectionError` / "Connection refused" → Ollama isn't running. Start `ollama serve`
  (step 4).
- A model-not-found error → you didn't pull the model (step 5), or you changed `model=` to
  something you haven't pulled. Run `ollama pull <name>`.
- First call is slow → Ollama is loading the model into memory; subsequent calls are fast.

## 8. (Optional) Tracing

If you set `LANGSMITH_TRACING=true` and `LANGSMITH_API_KEY`, every run in this course shows
up as a trace at <https://smith.langchain.com>. **Entirely optional** — no lab needs it, and
everything works without it. (This is the one piece that talks to the cloud; skip it to stay
fully local.)

---

If 1–7 pass, you're ready. 👉 **[Module 00: Setup & First Call](./00-setup/)**
