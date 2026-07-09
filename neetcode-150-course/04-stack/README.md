# Module 04 — Stack 🥞

**Goal:** master the LIFO container and the *monotonic stack* pattern. ⏱️ ~4 h
· 🎯 Prereq: 03.

```
stack: LIFO, O(1) push/pop, the right tool for "matching pairs" and "next greater/smaller"
```

---

## 1. Why a stack?

A stack is a **last-in, first-out** container. It shines when:

- The problem is about **matching pairs** (parentheses, tags, brackets).
- The problem asks "for each element, what's the next **bigger/smaller**?"
  → a *monotonic stack* gives an O(n) answer.
- You're simulating **nested** or **recursive** behavior (DFS, expression
  evaluation, undo history).

In Python the stack is just a `list` — `append` to push, `pop` to pop. In
Java we use `Deque<Integer>` via `ArrayDeque` (modern — `Stack` is legacy).

## 2. The 7 problems — easy → hard

| #  | Problem | Difficulty | Pattern |
|----|---------|-----------|---------|
| 01 | [Valid Parentheses](./problems/01-valid-parentheses/) | Easy | Match openers/closers |
| 02 | [Min Stack](./problems/02-min-stack/) | Medium | Design — pair (value, min) |
| 03 | [Evaluate Reverse Polish Notation](./problems/03-evaluate-reverse-polish-notation/) | Medium | Stack machine |
| 04 | [Generate Parentheses](./problems/04-generate-parentheses/) | Medium | Backtracking with stack (Module 10) |
| 05 | [Daily Temperatures](./problems/05-daily-temperatures/) | Medium | Monotonic stack — "next greater" |
| 06 | [Car Fleet](./problems/06-car-fleet/) | Medium | Sorted stack — "fleet time" |
| 07 | [Largest Rectangle in Histogram](./problems/07-largest-rectangle-in-histogram/) | Hard | Monotonic stack — nearest smaller |

## 3. The two templates

### Matching pairs

```python
stack = []
for c in s:
    if c is an opener:
        stack.append(c)
    else:
        if not stack or stack[-1] != matching(c):
            return invalid
        stack.pop()
return not stack
```

### Monotonic stack — "next greater" or "nearest smaller"

```python
stack = []   # indices, values monotone
for i, x in enumerate(arr):
    while stack and arr[stack[-1]] < x:   # condition depends on the problem
        j = stack.pop()
        answer[j] = i - j                # or similar
    stack.append(i)
```

The *condition* is what you tune:

- `arr[stack[-1]] < x`  → "next greater" (Daily Temperatures).
- `arr[stack[-1]] >= h` → "previous smaller" (Largest Rectangle).
- Other variants: "next smaller or equal", "previous greater", etc.

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Stack | `list` (with `.append` / `.pop`) | `Deque<T>` via `ArrayDeque<T>` |
| Push | `stack.append(x)` | `stack.push(x)` |
| Pop | `stack.pop()` | `stack.pop()` |
| Peek | `stack[-1]` | `stack.peek()` |
| Empty check | `not stack` | `stack.isEmpty()` |
| Stack of pairs | `list[tuple[int, int]]` | custom class or `int[]` |
| Division truncate-toward-zero | `int(a / b)` (not `a // b`) | `a / b` on `int` |
| Sort by 2nd key | `sorted(items, key=lambda x: x[1])` | `Arrays.sort(arr, comparator)` |

## 5. Common pitfalls

- **Empty stack on `pop`/`peek`.** Always check `isEmpty` first in Java.
- **Truncation direction.** `int(-1.5)` in Python is `-1`; `-3 // 2` is `-2`.
  The RPN problem explicitly says "truncate toward zero," so use
  `int(a / b)` in Python, not `a // b`.
- **Off-by-one with sentinels.** The largest-rectangle trick of appending a
  `0` is a sentinel — make sure your loop range includes it.
- **Strict vs non-strict inequality.** The condition
  `arr[stack[-1]] >= h` (largest rectangle) vs `<` (next greater) is the
  difference between a correct and an off-by-one answer.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then the [problems/](./problems/) in order.

## Key terms

LIFO · matching pairs · monotonic stack · next greater · nearest smaller ·
sentinel

**Next →** [Module 05: Binary Search](../05-binary-search/)
