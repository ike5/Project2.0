# VERIFY — confirm your environment works

Run these before Module 01. Each has an expected result. If one fails, the fix is
noted.

---

## 1. Python version

```bash
python3 --version
```

✅ You should see `Python 3.10` or higher. (Some exercises use `match` and
`|` union types.)

> If you have an older version, install Python 3.11+ from
> <https://www.python.org/downloads/> or via `pyenv`.

## 2. Create the course virtual environment

```bash
cd neetcode-150-course
python3 -m venv .venv
source .venv/bin/activate
```

✅ Your prompt should now be prefixed with `(.venv)`.

> On Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

✅ You should see `Successfully installed pytest-...`.

## 4. Confirm pytest is available

```bash
pytest --version
```

✅ You should see `pytest 7.x` or higher.

## 5. Java 21 install

```bash
java --version
javac --version
```

✅ Both should print `21.x.y` (or any 21+ version).

> Don't have it? On macOS:
> ```bash
> brew install --cask temurin@21
> export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
> ```
> Or download from <https://adoptium.net/>.

## 6. Run the Python smoke script

```bash
python 00-setup/code/hello_neetcode.py
```

✅ Expected:

```
hello, neetcode
two_sum([2, 7, 11, 15], 9) -> [0, 1]
```

## 7. Compile and run the Java smoke file

```bash
mkdir -p /tmp/verify-out
javac -d /tmp/verify-out 00-setup/code/HelloNeetCode.java
java -cp /tmp/verify-out HelloNeetCode
```

✅ Expected:

```
hello, java 21
two_sum([2, 7, 11, 15], 9) -> [0, 1]
```

If 1–7 pass, you're ready.

👉 **[Module 00: Setup & Orientation](./00-setup/)**
