# Verify Your Setup

Run these checks before starting the workbook.

## 1. Python version

```bash
python3 --version
```

You need **Python 3.8+**. If you see `Python 3.8.x` or higher, you're good.

## 2. Import check

```bash
python3 -c "import sys; sys.path.insert(0, 'code'); from workbook_engine import run_exercises; print('Engine imported OK')"
```

You should see `Engine imported OK`.

## 3. Quick lesson test

Pick any lesson and run it with a quick input to confirm it works:

```bash
cd lessons
echo "q" | python3 01_subjunctive_present.py
```

You should see the title banner and then "Session ended early." — this confirms the lesson loads and runs.

## 4. Run all lesson syntax checks

```bash
for f in lessons/*.py; do python3 -c "import py_compile; py_compile.compile('$f', doraise=True)" && echo "$f OK"; done
```

All files should report OK.

---

If everything passes, you're ready to start:

```bash
python3 lessons/01_subjunctive_present.py
```