# Python OOP Patterns for LeetCode & DSA 🐍🧩

A focused, code-first course that teaches the **Python skills** you need to solve Data Structures & Algorithms problems on LeetCode — taught through the lens of **object-oriented design patterns**.

> **Who this is for.** You're grinding LeetCode and you keep getting tripped up by Python-specific things: how dicts *really* work as hash maps, the difference between a class and a function, how `self` flows through a method call, why some `for` loops are O(n) and others are O(n²). You want a course that teaches Python *for DSA*, with OOP patterns as the spine.

---

## Why this course exists

Two things are true at the same time:

1. **Most LeetCode solutions don't need classes.** A `Two Sum` solution is often a 4-line function. An `LRU Cache` solution is a 60-line class. Both are real.
2. **The hard LeetCode problems are *design* problems.** "Design Twitter", "Design Hit Counter", "LRU Cache" — these are exercises in modeling state with the right Python containers (`dict`, `list`, `deque`, `OrderedDict`, `heapq`) and wrapping them in a clean class API.

So this course is built backwards from the problems. Every module:

- **Reinforces one Python skill** you absolutely need on LeetCode (dicts as maps, for-loop patterns, classes & `self`, list comprehensions, etc.)
- **Teaches one design pattern** that maps to a category of LeetCode problem (Strategy, Observer, Decorator, Factory, Adapter, Composition)
- **Closes with a LeetCode problem** that uses both

By the end you'll be able to read "Design a `Foo` class with `bar(x)` and `baz(y)` methods" and immediately know which Python container to reach for and which pattern to apply.

---

## The learning path

| #  | Module | Python skill you'll sharpen | Design pattern | LeetCode problem | Est. |
|----|--------|------------------------------|----------------|------------------|------|
| 00 | [Setup & DSA workflow](./00-setup/) | Running Python, REPL, `pytest`, reading LeetCode prompts | — | — | 30 min |
| 01 | [Dicts as hash maps](./01-dicts-as-maps/) | `dict` get/set, `defaultdict`, `Counter`, `dict` as a visited set | None (raw dict) | [1. Two Sum](https://leetcode.com/problems/two-sum/) | 1.5 h |
| 02 | [Loops & iteration patterns](./02-loops-and-iteration/) | `for`/`while`, `enumerate`, `range`, two-pointer, sliding window | None (raw loop) | [121. Best Time to Buy and Sell Stock](https://leetcode.com/problems/best-time-to-buy-and-sell-stock/) | 1.5 h |
| 03 | [Classes & `self`](./03-classes-and-self/) | Defining classes, `__init__`, `self`, instance vs class state | None (plain class) | [1603. Design Parking System](https://leetcode.com/problems/design-parking-system/) | 1.5 h |
| 04 | [The `__init__` strategy pattern](./04-strategy-pattern/) | Storing a callable / pluggable algorithm in `__init__` | **Strategy** | [1472. Design Browser History](https://leetcode.com/problems/design-browser-history/) | 1.5 h |
| 05 | [The subscriber / observer pattern](./05-observer-pattern/) | Storing a list of callables, broadcasting events | **Observer** | [362. Design Hit Counter](https://leetcode.com/problems/design-hit-counter/) | 1.5 h |
| 06 | [The wrapper / decorator pattern](./06-decorator-pattern/) | Wrapping an object to add behavior, `OrderedDict` | **Decorator** | [146. LRU Cache](https://leetcode.com/problems/lru-cache/) | 2 h |
| 07 | [The factory pattern](./07-factory-pattern/) | `classmethod`, registries, picking a class by name | **Factory** | [707. Design Linked List](https://leetcode.com/problems/design-linked-list/) | 1.5 h |
| 08 | [The adapter pattern](./08-adapter-pattern/) | Wrapping one interface behind another, list as a stack | **Adapter** | [155. Min Stack](https://leetcode.com/problems/min-stack/) | 1.5 h |
| 09 | [Iteration & comprehensions](./09-iteration-and-comprehensions/) | `sorted`, `key=`, generator expressions, `set` ops | None (functional) | [49. Group Anagrams](https://leetcode.com/problems/group-anagrams/) | 1.5 h |
| 10 | [Magic methods & iteration](./10-magic-methods/) | `__getitem__`, `__len__`, `__iter__`, `__contains__` | **Iterator protocol** | [622. Design Circular Queue](https://leetcode.com/problems/design-circular-queue/) | 2 h |
| 11 | [Composition over inheritance](./11-composition/) | Objects holding other objects, delegation, `dataclass` | **Composition** | [355. Design Twitter](https://leetcode.com/problems/design-twitter/) | 2 h |
| 12 | [Capstone: design a cache](./12-capstone/) | Combining dicts, `OrderedDict`, composition | All of the above | [460. LFU Cache](https://leetcode.com/problems/lfu-cache/) | 2 h |

**Total: ~21 hours.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts in plain language + the LeetCode problem
├── lab.md         ← Step-by-step guided lab with expected output
├── code/          ← Reference / starter code the lab uses
├── challenge.md   ← An unguided task to prove you understood it
└── solutions/     ← Reference answers — peek only after you've tried
```

**The rhythm for every module:**
1. Read `README.md` — the concept + the LeetCode problem statement.
2. Follow `lab.md` hands-on — run the code, modify it, see the output.
3. Attempt `challenge.md` solo — a tighter version of the lesson.
4. Check `solutions/` if you're stuck.
5. Open the LeetCode link and solve the problem in your own editor.

---

## The Python skills you'll build (LeetCode-flavored)

By the end of the course you should be *fluent* in:

- **Containers** — `list`, `dict`, `set`, `tuple`, `deque`, `Counter`, `defaultdict`, `OrderedDict`, `heapq`.
- **Iteration** — `for`, `enumerate`, `zip`, list/set/dict comprehensions, generator expressions.
- **Classes** — `__init__`, `self`, instance vs class attributes, methods, properties, `classmethod`, `staticmethod`.
- **Magic methods** — `__repr__`, `__eq__`, `__hash__`, `__len__`, `__getitem__`, `__iter__`, `__contains__`, `__enter__`/`__exit__`.
- **Patterns** — Strategy (pass a function), Observer (list of subscribers), Decorator (wrap an object), Factory (build by name), Adapter (translate an interface), Composition (delegate).
- **DSA idioms** — two pointers, sliding window, hash-map lookup, monotonic stack, BFS/DFS, in-place modification.

---

## Quick start

```bash
cd python-oop-patterns
python3 -m venv .venv
source .venv/bin/activate                  # Windows: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
cat README.md                              # ← you are here
cd 00-setup && cat README.md               # ← start the course
```

> If you don't have LeetCode Premium, every problem linked here is in the **free** problem set. You can read the full prompt on leetcode.com without an account.

Ready? **→ [Start with Module 00: Setup & DSA workflow](./00-setup/)**
