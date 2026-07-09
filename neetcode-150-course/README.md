# NeetCode 150: From Easy to Hard — Python & Java 21 🐍☕

A hands-on, code-first course that walks you through **all 130 problems** on the
[NeetCode 150](https://neetcode.io/) list (the canonical 14-topic set),
**solved in both Python and Java 21**,
organized **topic-by-topic, easy → medium → hard**.

> **Who this is for.** You're preparing for software engineering interviews and
> you want a single, well-structured resource that shows you the problem, the
> intuition, the algorithm, and a clean, idiomatic solution in **both** Python
> *and* modern Java 21. You do **not** need to know Java 21 deeply — the
> solutions use the modern features (records, `var`, `List.of`, etc.) so you
> pick them up as you go.

---

## Why this course

Most NeetCode-style resources are *videos* or *single-language* solution dumps.
This one is different:

- **Two languages, side by side.** Every problem ships a Python solution *and* a
  Java 21 solution. You read both, you compare, you internalize the idioms.
- **Easy → hard within each topic.** NeetCode's site lists topics and problems;
  this course reorders each topic so the first problem uses the simplest
  technique, the next one a slight twist, and so on. Difficulty grows inside
  the topic, not across the whole list.
- **Learn by doing.** Every module has a guided `lab.md`, an unguided
  `challenge.md`, and reference `solutions/` (in both languages) for every
  problem. The same rhythm as the other courses in this repo.
- **Local-first.** No LeetCode account required. Every solution is a single
  runnable file in each language. Clone, run, learn.

```
                ┌───────────────────────────────────────────┐
                │  Phase 0: Setup & Orientation              │
                │  (00-setup)                                 │
                └─────────────────────┬─────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                │   Phase 1: Building blocks (modules 01-04)  │
                │   Arrays & Hashing, Two Pointers,           │
                │   Sliding Window, Stack                     │
                └─────────────────────┬─────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                │   Phase 2: Search & structure (05-09)      │
                │   Binary Search, Linked List, Trees,        │
                │   Tries, Heap / Priority Queue              │
                └─────────────────────┬─────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                │   Phase 3: Recursion & state (10-12)       │
                │   Backtracking, Graphs, Dynamic Programming │
                └─────────────────────┬─────────────────────┘
                                      │
                ┌─────────────────────┴─────────────────────┐
                │   Phase 4: Optimization (13-14)            │
                │   Greedy, Intervals & Bit Manipulation      │
                └────────────────────────────────────────────┘
```

---

## What makes it effective

- **Topic-first, not difficulty-first.** You learn the *technique family*
  (e.g. two pointers, sliding window, BFS) in one module, then use it on five
  progressively harder problems. That mirrors how real interview prep works.
- **Bilingual by default.** Every solution is provided in **Python 3.10+** and
  **Java 21 (LTS)**. The Java solutions use modern features: `var`, records,
  `List.of`, `Map.of`, text blocks, pattern matching, and the standard
  collections. The Python solutions use type hints, `dataclass`, the standard
  library, and 3.10+ features where they help.
- **Idiomatic, not translated.** The Python and Java solutions are written as
  native speakers would write them — not as line-by-line translations. You
  learn the *idioms* of each language, not just the algorithm.
- **Self-testable.** Each problem has at least one or two `assert`s in its
  `main` method and a runnable script. No external test runner required for
  the first pass. (Module 00 shows the optional pytest workflow.)

---

## Prerequisites

- Comfort with one of the two languages (Python **or** Java). You can learn the
  other on the way — the labs point out language-specific gotchas.
- A terminal. Python 3.10+ and a JDK 21 (LTS) install.
- Curiosity and patience. 130 problems is roughly **70-90 hours** of focused
  work if you do every lab and challenge. Skim what you know; drill what you
  don't.

---

## The learning path

The 14 topic modules follow NeetCode's official categorization. Inside each
module, problems are ordered **easy → medium → hard**, so you never hit a
brutal problem before you've warmed up on its easier cousins.

### Phase 0 — Setup

| #  | Module | You'll learn to… | Est. |
|----|--------|------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Install Python 3.10+ and JDK 21, run a hello-world in each | 30 min |

### Phase 1 — Building blocks

| #  | Module | Problems | You'll learn to… | Est. |
|----|--------|----------|------------------|------|
| 01 | [Arrays & Hashing](./01-arrays-hashing/) | 9 | Hash maps, frequency counting, prefix products, design (LRU) | 6 h |
| 02 | [Two Pointers](./02-two-pointers/) | 5 | Opposite-end & same-direction pointers, in-place edits | 3 h |
| 03 | [Sliding Window](./03-sliding-window/) | 6 | Fixed and variable-size windows, frequency maps | 4 h |
| 04 | [Stack](./04-stack/) | 7 | Monotonic stacks, matching pairs, expression evaluation | 4 h |

### Phase 2 — Search & structure

| #  | Module | Problems | You'll learn to… | Est. |
|----|--------|----------|------------------|------|
| 05 | [Binary Search](./05-binary-search/) | 7 | Classic search, search-on-answer, two-pointer hybrid | 4 h |
| 06 | [Linked List](./06-linked-list/) | 11 | Fast/slow pointers, reversal, merge, design (LRU) | 6 h |
| 07 | [Trees](./07-trees/) | 15 | DFS/BFS, BST operations, recursive patterns, design | 8 h |
| 08 | [Tries](./08-tries/) | 3 | Prefix trees, backtracking on paths | 2 h |
| 09 | [Heap / Priority Queue](./09-heap-priority-queue/) | 7 | Top-K, two-heaps, scheduling | 4 h |

### Phase 3 — Recursion & state

| #  | Module | Problems | You'll learn to… | Est. |
|----|--------|----------|------------------|------|
| 10 | [Backtracking](./10-backtracking/) | 9 | Permutations, combinations, subsets, constraint propagation | 6 h |
| 11 | [Graphs](./11-graphs/) | 13 | BFS/DFS, Dijkstra, Union-Find, topological sort, design | 8 h |
| 12 | [Dynamic Programming](./12-dynamic-programming/) | 22 | 1D/2D DP, knapsack, LCS, intervals, bitmask | 14 h |

### Phase 4 — Optimization

| #  | Module | Problems | You'll learn to… | Est. |
|----|--------|----------|------------------|------|
| 13 | [Greedy](./13-greedy/) | 8 | Interval scheduling, jump game, two-pointer greedy | 4 h |
| 14 | [Intervals & Bit Manipulation](./14-intervals-bit-manipulation/) | 8 | Merge intervals, XOR tricks, bit counting | 4 h |

**Total: 130 problems · ~70-90 hours of focused work.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Topic overview, technique summary, problem list (easy → hard)
├── lab.md         ← Guided lab: worked examples and language comparisons
├── challenge.md   ← Unguided tasks to prove you understood the patterns
├── problems/      ← Per-problem briefs (one .md per problem)
├── code/          ← Runnable reference solutions — one Python + one Java file per problem
└── solutions/     ← Alternative solutions / detailed walkthroughs (per problem)
```

Inside each problem folder:

```
problems/01-two-sum/
├── README.md       ← the brief, examples, constraints, hints
solutions/01-two-sum/
├── solution.py     ← canonical Python solution
├── Solution.java   ← canonical Java 21 solution
└── walkthrough.md  ← step-by-step intuition, complexity, follow-ups
```

**The rhythm for every problem:** read the brief → try it on your own → look at
the walkthrough → read both solutions (Python *and* Java) → run them locally.

---

## Reference material (keep open)

- **[cheatsheets/python.md](./cheatsheets/python.md)** — Built-in containers,
  `bisect`, `heapq`, `defaultdict`, `Counter`, `dataclass`, sort key tricks.
- **[cheatsheets/java21.md](./cheatsheets/java21.md)** — `List.of`, `Map.of`,
  `Map.entry`, `Set.of`, `record`, `var`, `List.copyOf`, `Collections`, streams
  for competitive coding, `Arrays`.
- **[GLOSSARY.md](./GLOSSARY.md)** — Plain-English definitions of every term
  used in the course.
- **[VERIFY.md](./VERIFY.md)** — Run the smoke tests before Module 01.

---

## Quick start

```bash
# Clone (or work in this folder) and enter the course
cd neetcode-150-course

# Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Java 21
java --version    # 21.x.y
javac --version   # 21.x.y

# Sanity check
python 00-setup/code/hello_neetcode.py
java  00-setup/code/HelloNeetCode.java
```

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
