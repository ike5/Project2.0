# Glossary

Plain-English definitions of every term used in this course. Each entry points to the module where you'll see it used.

---

## Python containers

- **list** — Ordered, mutable sequence. `O(1)` append, `O(n)` insert/remove at front, `O(1)` index. The default "bag of stuff" in Python. *(Modules 02, 08, 09)*
- **dict** — Hash map from key to value. `O(1)` average get/set/delete. The single most important data structure in this course. *(Modules 01, 04, 05, 06, 10, 11, 12)*
- **set** — Hash set. `O(1)` membership test. Use it when you only care whether something is present, not what it maps to. *(Modules 01, 09)*
- **tuple** — Ordered, immutable sequence. Hashable, so it can be a dict key or a set element. *(Modules 09, 10)*
- **deque** — Double-ended queue from `collections`. `O(1)` append/pop on *both* ends; `O(n)` indexing. The right tool for BFS and sliding windows. *(Modules 02, 11)*
- **Counter** — `dict` subclass for counting hashable things. `Counter("aab")` → `{'a': 2, 'b': 1}`. *(Modules 01, 09)*
- **defaultdict** — `dict` that creates a default value for missing keys. `dd = defaultdict(list); dd["x"].append(1)`. *(Modules 01, 11)*
- **OrderedDict** — `dict` that remembers insertion order and supports `move_to_end`. The classic LRU building block. *(Module 06)*
- **heapq** — Min-heap on top of a list. `O(log n)` push/pop, `O(1)` peek. Use it for "k-th smallest" / Dijkstra. *(Module 12)*

## Iteration

- **for loop** — `for x in iterable:` — runs the body once per element. The workhorse of LeetCode. *(Module 02)*
- **enumerate** — `for i, x in enumerate(xs):` — gives you `(index, value)` pairs. Avoids the `range(len(xs))` anti-pattern. *(Module 02)*
- **zip** — `for a, b in zip(xs, ys):` — pairs up multiple iterables. *(Module 09)*
- **range** — `range(n)` is `[0, n)`; `range(a, b, step)` generalizes it. *(Module 02)*
- **comprehension** — `[f(x) for x in xs if pred(x)]` — list, set, dict, and generator variants. The Pythonic way to build a container. *(Module 09)*
- **two-pointer** — Walk two indices through a sequence (often from both ends) in `O(n)`. Classic for sorted arrays. *(Module 02)*
- **sliding window** — Maintain a window `[left, right)` over a sequence and slide it to satisfy a constraint. Often `O(n)`. *(Module 02)*

## Classes & OOP

- **class** — A blueprint for objects. `class Dog: ...` defines a `Dog` type. *(Module 03)*
- **instance** — A concrete object built from a class. `rex = Dog()` creates an instance. *(Module 03)*
- **`self`** — The first parameter of an instance method. Python passes the instance in automatically. *(Module 03)*
- **`__init__`** — The constructor. Called when you write `Dog()`. Use it to set up `self.x = ...`. *(Module 03)*
- **instance attribute** — A value stored on `self`. Each instance has its own copy. *(Module 03)*
- **class attribute** — A value stored on the class itself. Shared across all instances. *(Module 03)*
- **method** — A function defined inside a class. Receives `self` (or `cls` for `classmethod`) as its first argument. *(Modules 03, 05)*
- **staticmethod** — A function inside a class that doesn't get `self` or `cls`. Just a name on the class. *(Module 07)*
- **classmethod** — A method that gets the class itself (`cls`) instead of an instance. Common in factory methods. *(Module 07)*
- **inheritance** — A class that reuses and extends another. `class Puppy(Dog): ...`. *(Module 11)*
- **composition** — A class that *holds* another class as a field. `self.tail = Tail()`. Preferred over inheritance when the relationship is "has-a" not "is-a". *(Modules 06, 11)*
- **dataclass** — `@dataclass class Point: x: int; y: int` — auto-generates `__init__`, `__repr__`, `__eq__`. *(Module 11)*
- **Protocol** — A structural-typing base class. Anything with the right methods counts as a `Protocol` subtype, no inheritance required. *(Module 04)*

## Magic methods (dunder methods)

- **`__repr__`** — Developer-facing string. `repr(obj)`. Aim for unambiguous. *(Module 10)*
- **`__str__`** — User-facing string. `str(obj)`, `print(obj)`. *(Module 10)*
- **`__eq__`** — `obj1 == obj2`. Define it when you want value equality. *(Module 10)*
- **`__hash__`** — `hash(obj)`. If you define `__eq__`, `__hash__` is set to `None` and the object becomes unhashable (no dict keys!). *(Module 10)*
- **`__len__`** — `len(obj)`. *(Module 10)*
- **`__getitem__`** — `obj[key]`. Define it and your object is iterable too. *(Module 10)*
- **`__iter__`** — `for x in obj:`. Define it and your object works anywhere an iterable is expected. *(Module 10)*
- **`__contains__`** — `x in obj`. *(Module 10)*

## Design patterns (Gang of Four, Python-flavored)

- **Strategy** — Pass an algorithm (function or object) into another object so the algorithm is pluggable. LeetCode flavor: a class that takes a callable in `__init__`. *(Module 04)*
- **Observer** — One object (the subject) keeps a list of subscribers and calls them on events. LeetCode flavor: a counter that records events and answers range queries. *(Module 05)*
- **Decorator** — Wrap an object to add behavior without changing the original. LeetCode flavor: an LRU cache wraps a plain `dict` with eviction. *(Module 06)*
- **Factory** — A method that builds and returns the right subclass based on a name. LeetCode flavor: `LinkedList.from_array(xs)`. *(Module 07)*
- **Adapter** — Wrap an object so it presents a different interface. LeetCode flavor: a `MinStack` adapts a normal `list` to track minimums. *(Module 08)*
- **Composition** — Build complex objects by combining simpler ones. LeetCode flavor: a `Twitter` class that holds a `deque` of tweets per user. *(Module 11)*

## LeetCode / DSA vocabulary

- **time complexity** — How the running time scales with input size. `O(1)`, `O(log n)`, `O(n)`, `O(n log n)`, `O(n²)`, `O(2ⁿ)`.
- **space complexity** — How the extra memory scales.
- **in-place** — Modify the input directly, using `O(1)` extra space.
- **two-pointer** — see above.
- **sliding window** — see above.
- **hash map** — Synonym for `dict` in Python.
- **visited set** — A `set` of nodes/indices you've already seen, to avoid re-processing.
- **BFS** — Breadth-first search. Use a `deque`.
- **DFS** — Depth-first search. Use a stack (or recursion).

---

> **How to use this file.** Skim it once before Module 00 so the vocabulary doesn't surprise you. Come back to it whenever a term in a module's README is unfamiliar.
