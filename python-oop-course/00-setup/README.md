# Module 00 — Setup & Orientation

**Goal:** Get a working Python environment, a virtualenv, and `pytest` installed — and confirm you can run a small script and a small test. ⏱️ ~30 min.

---

## 1. Why a venv?

Every Python project should live in its own **virtual environment** (a `venv`). A venv is a self-contained directory that holds a copy of the Python interpreter *and* a private set of installed packages. Two reasons this matters:

- **Isolation.** The OOP course installs `pytest`. Another project might install a different version. venvs keep them from clobbering each other.
- **Reproducibility.** A `requirements.txt` plus a venv means a teammate (or you, six months from now) can recreate exactly the same environment with two commands.

The course ships a `requirements.txt` at the repo root. You'll `pip install` from it once and forget about it.

> **Note:** if you already have a global Python and you're comfortable without a venv, you can skip the venv step. But the labs assume one is active.

## 2. Project layout you'll build toward

By Module 02 you'll be writing files in a `code/` folder. By Module 11 you'll have a multi-module project. Here's the shape:

```
python-oop-course/
├── 00-setup/
│   ├── README.md          ← you are here
│   ├── lab.md
│   ├── code/              ← runnable scripts
│   └── solutions/
├── 01-oop-foundations/...
├── ...
├── 11-capstone/...
├── cheatsheets/
├── tests/                 ← you'll add a tests/ folder in Module 10
├── .venv/                 ← created by you, ignored by git
├── .gitignore
├── requirements.txt
├── README.md
├── GLOSSARY.md
└── VERIFY.md
```

The `00-setup/code/` folder has a tiny "hello, oop" script. The `00-setup/solutions/` folder has the same thing with a small test you can run with `pytest`.

## 3. The `if __name__ == "__main__":` idiom

Every script in this course ends with:

```python
if __name__ == "__main__":
    main()
```

The double-underscore variable `__name__` is set by Python. When you run a file directly, `__name__` is `"__main__"`. When the file is *imported* by another module, `__name__` is the module's name. That means:

- Running `python my_script.py` executes `main()`.
- Importing `from my_script import foo` does **not** execute `main()`.

This lets you write a file that runs as a script *and* gets imported as a library without side effects. You'll use it constantly.

## 4. How the labs work

A "lab" is a guided walk-through. Each part is a small, runnable exercise with an **expected output** (marked `✅`). You'll be told exactly what commands to type and what you should see. The goal isn't to make you memorize; it's to build muscle memory and let you *see* that things work before you try them on your own.

After a lab comes a `challenge.md`: an unguided task. The solutions are in `solutions/`, but try first.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/hello_oop.py`](./code/hello_oop.py) — a one-screen script that defines a class, creates an instance, and calls a method.
- [`code/run_with_pytest.py`](./code/run_with_pytest.py) — a one-screen test that asserts something about a class.

## Key terms

venv · `__name__ == "__main__"` · `requirements.txt` · `pytest` · `pip` · `python -m`

**Next →** [Module 01: OOP Foundations](../01-oop-foundations/)
