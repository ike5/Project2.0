# Lab 00 — Setup & Orientation

**You'll:** confirm Python and Java 21 both work, and run a "hello" Two Sum in
each. ⏱️ ~20 min.

Run from the `neetcode-150-course/` folder.

---

## Part A — Confirm Python

```bash
python3 --version
```

✅ Should print `Python 3.10` or higher.

## Part B — Set up a virtualenv (optional but recommended)

```bash
cd neetcode-150-course
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

✅ Your prompt should be prefixed with `(.venv)`.
✅ `pip install` should report `Successfully installed pytest-...`.

> On Windows (PowerShell): `.\.venv\Scripts\Activate.ps1`
> To deactivate later, just run `deactivate`.

## Part C — Run the Python smoke script

```bash
python 00-setup/code/hello_neetcode.py
```

✅ Expected output:

```
hello, neetcode
two_sum([2, 7, 11, 15], 9) -> [0, 1]
two_sum([3, 2, 4], 6)        -> [1, 2]
two_sum([3, 3], 6)          -> [0, 1]
```

> The `two_sum` function here is the *one-pass hash map* version. You'll see
> it in detail in Module 01.

## Part D — Confirm Java 21

```bash
java --version
javac --version
```

✅ Both should print `21.x.y` (or any 21+ version).

## Part E — Compile and run the Java smoke file

```bash
mkdir -p /tmp/out
javac -d /tmp/out 00-setup/code/HelloNeetCode.java
java -cp /tmp/out HelloNeetCode
```

✅ Expected output:

```
hello, java 21
two_sum([2, 7, 11, 15], 9) -> [0, 1]
two_sum([3, 2, 4], 6)        -> [1, 2]
two_sum([3, 3], 6)          -> [0, 1]
```

The Java file lives in the *default package* (no `package` line) so we can
compile and run it from anywhere without directory-prefix bookkeeping. We use
`/tmp/out` as the destination; you can use any empty directory.

## Part F — Optional: run the tests with pytest

We don't lean on pytest in this course — most solutions are runnable scripts
with built-in `assert`s. But it's good to know it works:

```bash
pytest --version
```

✅ Should print `pytest 7.x` or higher.

## Cleanup

Nothing to clean up. To remove the venv later: `rm -rf .venv`.

## What you learned

- A venv isolates per-project Python dependencies.
- The Python smoke file defines `two_sum` as a one-pass hash map.
- The Java smoke file does the same in `HelloNeetCode.twoSum`, compiled and
  run with `javac` and `java`.
- Each Java file in this course is a single public class with a `main` method
  in the default package, so you can compile and run without ceremony.

➡️ **[challenge.md](./challenge.md)** then [Module 01: Arrays & Hashing](../01-arrays-hashing/).
