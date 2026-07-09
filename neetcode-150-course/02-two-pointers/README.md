# Module 02 — Two Pointers 👉👈

**Goal:** master the most flexible interview pattern — *two indices walking
through a sequence*. ⏱️ ~3 h · 🎯 Prereq: 01.

```
two pointers: O(n²) brute force → O(n) sorted scan
```

---

## 1. Why this module second?

The **two pointers** technique is the single biggest "level up" you can make
after arrays-and-hashing. Many problems that look O(n²) on the surface
collapse to a single linear pass when you maintain two indices that move
*toward* or *away* from each other.

The two flavors:

- **Opposite ends** — `l` at 0, `r` at n-1, both move toward the middle.
  Used when the input is **sorted** or when the problem has a natural
  "wide → narrow" structure (palindromes, container, water).
- **Same direction (fast/slow)** — both start at 0 but move at different
  speeds. Used for *in-place* edits and *cycle detection* (linked list,
  Module 06). We touch it in Module 06; this module focuses on opposite-ends.

## 2. The 5 problems — easy → hard

| #  | Problem | Difficulty | Pattern |
|----|---------|-----------|---------|
| 01 | [Valid Palindrome](./problems/01-valid-palindrome/) | Easy | Skip & compare, opposite ends |
| 02 | [Two Sum II — Sorted Input](./problems/02-two-sum-ii-input-array-is-sorted/) | Easy | Sum, advance the right pointer |
| 03 | [3Sum](./problems/03-three-sum/) | Medium | Sort + fix one, two-pointer the rest |
| 04 | [Container With Most Water](./problems/04-container-with-most-water/) | Medium | Greedy: move the shorter side |
| 05 | [Trapping Rain Water](./problems/05-trapping-rain-water/) | Hard | Running max from each side |

## 3. The two templates

### Opposite ends — sorted, "find a pair"

```python
l, r = 0, len(nums) - 1
while l < r:
    if condition:
        ...
        return ...
    if move_left:
        l += 1
    else:
        r -= 1
```

### Greedy — "advance the worse side"

```python
while l < r:
    if nums[l] < nums[r]:
        ...   # l is the bottleneck; advance it
        l += 1
    else:
        ...   # r is the bottleneck; advance it
        r -= 1
```

`Container With Most Water` and `Trapping Rain Water` use this template.

## 4. The sorting trick

Three of the five problems **sort the input first**. Sorting is O(n log n)
but it unlocks the O(n) two-pointer pass. Total: O(n log n). When the input
is already sorted, you save the sort.

## 5. Common pitfalls

- **Off-by-one on the result.** The `Two Sum II` problem wants **1-indexed**
  output. The trick: add 1 only when returning, not when incrementing.
- **Duplicate handling.** `3Sum` requires unique triplets. Skip duplicates
  at every level (outer `i`, inner `l`, inner `r`).
- **Moving the wrong pointer.** In `Container With Most Water`, moving the
  *taller* line can never help — only the *shorter* line can produce a
  larger area in a future step.
- **Empty or single-element input.** Always make sure your loop guard
  handles `n < 2`.

## 6. Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Swap two list elements | `a[l], a[r] = a[r], a[l]` | needs a temp or `Collections.swap` |
| Sort in place | `nums.sort()` | `Arrays.sort(nums)` |
| Sort copy | `sorted(nums)` | `nums.clone()`, then `Arrays.sort` |
| Min/max | `min(a, b)` | `Math.min(a, b)` / `Math.max(a, b)` |
| Output as list | `[...]` | `Arrays.asList(...)` / new `ArrayList<>(...)` |
| Output array | `[1, 2, 3]` | `new int[]{1, 2, 3}` or `new Integer[]{1, 2, 3}` |

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then the [problems/](./problems/) in order.

## Key terms

two pointers · opposite ends · same direction · fast/slow ·
greedy · sorting trick · skip duplicates

**Next →** [Module 03: Sliding Window](../03-sliding-window/)
