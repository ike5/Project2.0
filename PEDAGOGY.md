# Pedagogy

This document defines the pedagogical framework used by every course in this
repository. **Read this before creating or modifying any course content.** All
16 courses follow these conventions — consistency is what makes the curriculum
feel like one system rather than a pile of unrelated tutorials.

---

## Core philosophy

1. **Learn by doing.** Every concept lands in a runnable script, a deployed
   manifest, a styled component, or a solved problem. No passive reading, no
   abstract theory without something to run. The student should spend 80%+ of
   their time doing, 20% reading.

2. **Production patterns, not toys.** We teach what real practitioners use:
   layered architecture, RBAC, observability, CI/CD, HA databases, idempotent
   automation. We don't stop at "Hello World" and call it a course.

3. **Deliberate failure.** Several courses teach students to break things on
   purpose — roll back a broken deployment, kill a database primary, deploy a
   nonexistent image tag, debug `CrashLoopBackOff`. Debugging is the job; we
   practice it from day one.

4. **Local-first.** Every course runs on a single laptop (Mac or Linux) with
   free tools. No cloud accounts, no paid APIs, no enterprise licenses required.
   Kubernetes uses `kind`, databases use Docker Compose, ML runs on CPU.

5. **Modern and idiomatic.** Java 21 (not Java 8), Python 3.10+ (not 2.7),
   Spring Boot 3 (not 2), Unity 6 LTS, C# 12. We teach current versions and
   reject legacy patterns.

---

## Universal module structure

Every module — in every course — follows this exact four-file pattern:

```
NN-topic/
  README.md       ← Concepts in plain language. Read first.
  lab.md          ← Step-by-step guided lab with expected output. Do second.
  challenge.md    ← An unguided task to prove you understood. Do third.
  solutions/      ← Reference answers — peek only after you've tried.
```

Some courses add supporting files inside the module directory:
- `code/` or `manifests/` — starter/reference files the lab uses
- `demo.html` — self-contained interactive demos (CSS course)
- `problems/` — per-problem briefs (NeetCode course)

### The learning rhythm

Every module is completed in this order:

1. **Read `README.md`** — understand the concepts, vocabulary, and mental models.
2. **Follow `lab.md`** — run the commands, write the code, see expected output.
3. **Attempt `challenge.md`** — apply the concepts solo without guidance.
4. **Check `solutions/`** — compare your work to the reference. Only after trying.

This rhythm never changes. The student should know exactly what to do when they
enter any module directory, regardless of which course they're in.

---

## Course-level structure

Every course follows this top-level pattern:

### README.md (course overview)

Each course README includes:
- **Title** with a distinctive emoji
- **"Who this is for"** — the target learner and their starting point
- **"Why this course"** — what differentiates it from alternatives
- **ASCII arc diagram** — a visual flowchart of the learning progression
- **Prerequisites** — what the student needs before starting
- **Learning path table** — all modules listed with estimated time
- **Module structure** — the four-file pattern explained
- **Reference material** — cheatsheets and glossary listed
- **Philosophy** — what the course values (learn by doing, production patterns, etc.)

### Supporting files (every course)

| File | Purpose |
|------|---------|
| `GLOSSARY.md` | Plain-English definitions of every domain-specific term, organized by topic |
| `VERIFY.md` | End-to-end smoke test: step-by-step commands with expected output to confirm the environment works |
| `cheatsheets/` | Concise reference cards — CLI syntax, command summaries, troubleshooting decision trees |

---

## Phases and progression

Courses are organized into **phases** that build incrementally:

- **Phase 0** is always **Setup & Orientation** — install the toolchain, confirm
  the environment works, orient in the domain.
- Earlier modules establish foundations; later modules combine them.
- Difficulty ramps within each topic (e.g., NeetCode: Easy → Medium → Hard
  inside each module, not across the whole course).
- Every course ends with a **capstone module** that synthesizes all prior
  learning into a real, complete project.

### Capstone projects

Every course culminates in a capstone that ties everything together:

| Course | Capstone |
|--------|----------|
| Kubernetes | Full multi-tier deployment on a multi-node cluster |
| Ansible | Load-balanced multi-host web deployment |
| Java OOP | Library Management System |
| Python OOP | Library management system with CLI and tests |
| .NET | Supported Web API + playable Unity game |
| Spring Boot | Production-ready, containerized, observable app |
| Slack Clone | Full real-time chat on a high-availability Kubernetes cluster |
| CSS Buttons | Complete button design system (variants, sizes, states, dark mode) |
| ML/PyTorch | Trained image classifier with a TensorBoard experiment report |
| Linux | Hardened web server with firewall, logging, and backups |
| Unity Senior | Small production-grade game |
| NeetCode 150 | Portfolio of 130 solved problems in two languages |

---

## Teaching strategies

### Progressive scaffolding

Concepts build on each other. A module assumes the student completed every prior
module. Early modules are narrow and concrete; later modules are broader and
more open-ended.

### Deliberate breaking / failure-driven learning

Several courses intentionally teach students to break things:
- Kubernetes: "Update the image to a tag that doesn't exist — observe what happens."
- .NET: "Fix a deliberately broken app."
- Slack Clone: "Kill the database primary on purpose — watch it heal."

This is pedagogy, not an accident. Students learn more from debugging than from
watching things work.

### Cross-course dependencies (spiral curriculum)

Courses explicitly reference and build on each other:
- Linux → Ansible ("automate exactly the work you learn there")
- .NET → Unity basics → Swift/iOS Unity embedding → Unity Senior deep dive
- Python OOP Patterns is a companion to NeetCode 150
- Kubernetes is a prerequisite for the Slack Clone course
- Linux + Kubernetes + Ansible form a DevOps pathway

When writing a new course, check if it fits into an existing dependency chain
and cross-reference related courses.

### Visual learning integration

- TensorBoard is wired in from Module 02 of the ML course for live visualization
- CSS course has `demo.html` files and a live playground sandbox
- ASCII diagrams in READMEs show the course arc visually
- Mermaid diagrams in Kubernetes and other lessons (flowcharts, architecture)

### Multi-language comparison (where applicable)

The NeetCode course provides every solution in both Python 3.10+ and Java 21,
written **idiomatically** — not as line-by-line translations. Students learn the
idioms of each language, not just the algorithm.

### Retrieval practice and spaced repetition (Spanish workbook)

The Spanish workbook is the most algorithmically sophisticated course:
- SQLite-backed progress tracking with retry logic
- First try correct = mastered, wrong + retry correct = learning, twice wrong = revealed
- Fuzzy matching on answers (accent/punctuation tolerance)
- Analytics dashboard: mastery levels, weak spots, learning trends, 95% confidence
  intervals, spaced repetition suggestions, retention tracking

---

## Content writing conventions

### Module README.md

- Start with a one-line goal statement: "Master [X] so you can [Y]."
- Include estimated time and prerequisites (which prior modules).
- Explain concepts in **plain language** — define every term on first use.
- Use diagrams (ASCII, Mermaid, or both) for architecture and relationships.
- End with a "See you in the lab" or equivalent pointer to `lab.md`.

### lab.md

- Begin with a summary of what the student will do and how long it takes.
- Break into labeled parts (Part A, Part B, Part C...).
- Every command or code block should be followed by expected output
  (marked with a checkmark or "Expected:").
- Include brief explanations of *why* something works, not just *what* to type.
- Do not skip steps — if a file needs to be created, show creating it.

### challenge.md

- Start with: "Solutions in [`solutions/`](./solutions/). Try first."
- Define 2–4 clear, numbered tasks with concrete success criteria.
- Include a checkbox-style "Success criteria" section at the bottom.
- Challenges should be solvable with the concepts from the module but require
  original thought — no copy-paste from the lab.
- Include at least one "stretch" task for students who finish early.

### solutions/

- One file per task (or one file with clearly separated sections).
- Should be runnable/runnable-as-given where applicable.
- Include brief comments explaining non-obvious choices, but not line-by-line
  narration.

---

## Domain-specific patterns

### Programming courses (Python OOP, Java OOP, .NET, Swift)

- Teach one language or paradigm deeply — don't spread thin.
- Every concept gets a complete, runnable script. No half-finished snippets.
- Include testing (pytest, JUnit, etc.) as a first-class concern, not an afterthought.
- Capstone is a real application with tests, not a toy.

### Infrastructure courses (Linux, Ansible, Kubernetes)

- Teach on real systems — VMs, multi-node clusters, real packages.
- Include troubleshooting decision trees in cheatsheets.
- Safety-first: rollback before creative deployment, idempotence as a mindset.
- Dual-distro support where relevant (Debian/Ubuntu + RHEL/Fedora).

### Web/full-stack courses (Spring Boot, Slack Clone)

- Build one real application across all modules — no throwaway toys.
- Teach the full dependency graph, not just the starter.
- Include production concerns: auth, observability, CI/CD, HA, testing.
- Containerize and deploy as a natural part of the course.

### Game development courses (Unity, .NET+Unity)

- Code lives under a dedicated scripts directory; never commit build artifacts.
- Teach production patterns: memory budgets, profiling, asset pipelines.
- Senior-level courses assume programming experience; don't re-teach basics.

### ML/data science courses (PyTorch)

- Visualize everything — TensorBoard from Module 02 onward.
- Build intuition before math: "see the gradient descend" before deriving it.
- CPU-only by default; GPU optional and auto-detected.
- Capstone includes a written experiment report, not just a trained model.

### Language learning (Spanish workbook)

- Interactive Python scripts as the delivery mechanism — not PDFs or web apps.
- Retry logic and fuzzy matching for answer checking.
- SQLite-backed progress tracking with analytics.
- Focus on a specific dialect, not generic "standard" language.

---

## Scale and consistency

| Metric | Target |
|--------|--------|
| Modules per course | 8–18 |
| Estimated hours per course | 16–70 |
| Module structure | Always the same four files |
| Learning rhythm | README → lab → challenge → solutions |
| Capstone | Always present, always synthesizes all modules |
| GLOSSARY.md | Always present, plain-English definitions |
| VERIFY.md | Always present, step-by-step environment check |
| cheatsheets/ | Always present, concise reference cards |

---

## Checklist for creating a new course

Before shipping a new course, verify:

- [ ] Course README.md follows the template (title, emoji, who, why, arc, prereqs, table, structure)
- [ ] Module 00 is always Setup & Orientation
- [ ] Every module has all four files: README.md, lab.md, challenge.md, solutions/
- [ ] Every lab command includes expected output
- [ ] Every challenge has numbered tasks + success criteria
- [ ] GLOSSARY.md exists with plain-English definitions for every term
- [ ] VERIFY.md exists with step-by-step environment validation
- [ ] cheatsheets/ directory has at least a CLI/syntax reference and a troubleshooting guide
- [ ] A capstone module synthesizes all prior learning
- [ ] Cross-references to related courses exist where applicable
- [ ] ASCII or Mermaid arc diagram is in the course README
- [ ] Estimated time for each module and total is included
- [ ] Modern tool versions only — no legacy patterns
- [ ] All content is runnable locally with free tools
