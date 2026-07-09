# Module 00 — Setup & Orientation

**Goal:** Get a working **Python 3.10+** environment and a **JDK 21 (LTS)**
install, and confirm you can run a small "hello neetcode" script in each
language. ⏱️ ~30 min.

---

## 1. Why Python AND Java?

This course is bilingual. Every problem ships a **Python** solution and a
**Java 21** solution. You learn the algorithm *and* the language idioms at the
same time. The two languages are good for different reasons:

- **Python** — terse, batteries-included, great for prototyping. The
  `collections`, `heapq`, and `bisect` modules cover 80% of interview needs.
- **Java 21** — explicit, strongly-typed, runs fast. Modern features (records,
  `var`, `List.of`, pattern matching) make it concise enough for interview
  coding without sacrificing the type-safety interviewers expect at big tech
  companies.

You don't need to know either deeply coming in. You need to know at least one.

## 2. What you're installing

| Tool | Version | Why |
|------|---------|-----|
| **Python** | 3.10 or newer | Solutions, tests, the labs |
| **JDK 21 (LTS)** | 21.x.y | Compile and run the Java solutions |
| **A terminal + text editor** | — | You already have these |
| **pytest** *(optional)* | 7.x+ | Run the smoke tests (skip if you like) |

> **Don't have JDK 21?** See the [VERIFY.md](./../VERIFY.md) for the install
> commands. On macOS:
> ```bash
> brew install --cask temurin@21
> export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
> ```
> Or download from <https://adoptium.net/>.

## 3. Project layout

```
neetcode-150-course/
├── 00-setup/
│   ├── README.md         ← you are here
│   ├── lab.md            ← guided lab
│   ├── challenge.md      ← unguided task
│   ├── code/             ← runnable smoke scripts
│   │   ├── hello_neetcode.py
│   │   └── HelloNeetCode.java
│   └── solutions/
├── 01-arrays-hashing/
│   ├── README.md         ← topic overview
│   ├── lab.md            ← worked example
│   ├── challenge.md      ← unguided task
│   ├── problems/         ← briefs, one per problem
│   ├── code/             ← reference Python + Java solutions
│   └── solutions/        ← walkthroughs
├── 02-two-pointers/ ...
├── ...
├── 14-intervals-bit-manipulation/
├── cheatsheets/
│   ├── python.md
│   └── java21.md
├── README.md             ← the entry point — start there
├── GLOSSARY.md
├── VERIFY.md
├── requirements.txt
└── .gitignore
```

The smoke files in `00-setup/code/` are the simplest possible "Two Sum" in each
language, just to confirm the toolchain works.

## 4. The shape of every problem in this course

```
problems/NN-problem-name/
├── README.md       ← the brief: problem statement, examples, constraints, hints

solutions/NN-problem-name/
├── solution.py     ← canonical Python solution
├── Solution.java   ← canonical Java 21 solution
└── walkthrough.md  ← intuition, complexity, follow-up questions
```

Every Python file is runnable as `python path/to/solution.py`. Every Java file
is one top-level public class with a `main` method. To run a Java file:

```bash
mkdir -p /tmp/out
javac -d /tmp/out path/to/Solution.java
java -cp /tmp/out Solution
```

The `main` method of each Java solution runs at least one example and prints
the result.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

JDK · LTS · virtualenv · `javac` / `java` · `pytest` · `main` method ·
classpath

**Next →** [Module 01: Arrays & Hashing](../01-arrays-hashing/)
