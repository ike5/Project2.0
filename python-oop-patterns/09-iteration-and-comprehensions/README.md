# Module 09 — Iteration & comprehensions

**Python skill:** `sorted`, `key=`, generator expressions, `set` ops, comprehensions.
**LeetCode problem:** [49. Group Anagrams](https://leetcode.com/problems/group-anagrams/) · Medium.
**Time:** ~1.5 h.

---

## 1. Comprehensions

A comprehension builds a new collection from an iterable. Python has four flavors:

```python
# list
[x * x for x in xs if x > 0]

# set
{ch for ch in s if ch.isalpha()}

# dict
{x: x * x for x in xs}

# generator (lazy, no brackets)
sum(x * x for x in xs)
```

The general form is `[<expr> for <var> in <iter> if <cond>]`. Multiple `for`s and `if`s are allowed but quickly become unreadable.

## 2. `sorted` with `key=`

`sorted` takes an optional `key=` function that extracts a sort key:

```python
words = ["fig", "apple", "kiwi"]
sorted(words)                              # ['apple', 'fig', 'kiwi']      (lexicographic)
sorted(words, key=len)                     # ['fig', 'kiwi', 'apple']     (by length)
sorted(words, key=lambda w: w[-1])         # ['apple', 'fig', 'kiwi']     (by last letter)
```

`min` and `max` take the same `key=`:

```python
max(words, key=len)                        # 'apple'
min(words, key=lambda w: w[-1])            # 'apple'
```

This is the same idea as the strategy pattern (Module 04), just applied to ordering.

## 3. Set operations

`set` supports `|`, `&`, `-`, `^` for union, intersection, difference, symmetric difference:

```python
a = {1, 2, 3}
b = {2, 3, 4}
a & b              # {2, 3}      intersection
a | b              # {1, 2, 3, 4} union
a - b              # {1}         in a but not in b
a ^ b              # {1, 4}      in one but not both
```

These are the bread and butter of problems like "find common elements", "find unique elements", "set cover", etc.

## 4. Generators

A generator expression `(x for x in xs)` is *lazy* — it doesn't build a list, it produces values one at a time. Useful when:

- The list would be huge.
- You only need the first match.
- You're chaining `any`, `all`, `sum`, `min`, `max`, etc.

```python
any(x > 100 for x in xs)        # stops at the first match
all(x > 0 for x in xs)          # stops at the first failure
sum(x * x for x in xs)          # never builds the list
next(x for x in xs if x > 100)  # first match
```

`next(gen, default)` returns the default if the generator is exhausted.

## 5. The LeetCode problem

> [49. Group Anagrams](https://leetcode.com/problems/group-anagrams/)
>
> Given an array of strings `strs`, group the anagrams together. You can return the answer in **any order**.

Two strings are anagrams iff their sorted versions are equal:

```python
from collections import defaultdict

def group_anagrams(strs: list[str]) -> list[list[str]]:
    groups: defaultdict[str, list[str]] = defaultdict(list)
    for s in strs:
        key = "".join(sorted(s))
        groups[key].append(s)
    return list(groups.values())
```

That's the whole problem. The "pattern" here isn't a GoF one — it's *just good Python*: `defaultdict` to group, `sorted` to build the key, comprehension to get the final shape.

## 6. Anti-patterns

- **Looping to build a list, then doing one more loop over it.** Comprehensions usually do both in one pass.
- **`list.sort()` and forgetting it's in-place.** It returns `None`. Use `sorted(...)` if you want a new list.
- **`{x: x for x in xs}` when `xs` is already a set of unique elements.** You don't need a comprehension — just use the set.
- **Sorting by hand with two nested loops.** `sorted` is C-level fast.

---

**→ Next: [Module 10 — Magic methods & iteration](./../10-magic-methods/)**
