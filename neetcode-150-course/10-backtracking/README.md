# Module 10 — Backtracking 🔙

**Goal:** build solutions by trying choices and undoing them when they
don't work. ⏱️ ~6 h · 🎯 Prereq: 09.

```
backtracking: try, recurse, undo — the right tool for "all possible" outputs
```

---

## 1. What is backtracking?

A backtracking algorithm builds a partial solution step by step. At each
step, it tries every possible choice; if a choice can't lead to a valid
solution, it **undoes** that choice and tries another. It's DFS over a
**state-space tree**.

Two flavors:

- **Decision at each index** (subsets, permutations): at index `i`, try
  every value.
- **Cut the search** when a partial solution is infeasible (N-Queens,
  Word Search).

## 2. The 9 problems — medium → hard

| #  | Problem | Difficulty | Pattern |
|----|---------|-----------|---------|
| 01 | [Subsets](./problems/01-subsets/) | Medium | Include/skip per element |
| 02 | [Combination Sum](./problems/02-combination-sum/) | Medium | Allow reuse |
| 03 | [Combination Sum II](./problems/03-combination-sum-ii/) | Medium | Sort, skip duplicates |
| 04 | [Permutations](./problems/04-permutations/) | Medium | Try each unused element |
| 05 | [Subsets II](./problems/05-subsets-ii/) | Medium | Sort, skip duplicates |
| 06 | [Word Search](./problems/06-word-search/) | Medium | 2D DFS, mark/unmark |
| 07 | [Palindrome Partitioning](./problems/07-palindrome-partitioning/) | Medium | DP table + backtrack |
| 08 | [Letter Combinations of a Phone Number](./problems/08-letter-combinations-of-a-phone-number/) | Medium | Try each letter |
| 09 | [N-Queens](./problems/09-n-queens/) | Hard | Row by row, attack sets |

## 3. The two patterns

### Pattern 1: include/skip

```python
def backtrack(i, path):
    if i == len(nums):
        out.append(path.copy())
        return
    # skip
    backtrack(i + 1, path)
    # include
    path.append(nums[i])
    backtrack(i + 1, path)
    path.pop()
```

### Pattern 2: try each choice

```python
def backtrack(state):
    if is_complete(state):
        record(state)
        return
    for choice in choices(state):
        if not is_valid(choice, state): continue
        apply(choice, state)
        backtrack(state)
        undo(choice, state)
```

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Add to list | `path.append(x)` | `path.add(x)` |
| Remove last | `path.pop()` | `path.remove(path.size() - 1)` |
| Copy list | `path.copy()` | `new ArrayList<>(path)` |
| String builder | `''.join(parts)` | `StringBuilder` + `append` / `deleteCharAt` |
| Sort and check duplicate | `if j > i and nums[j] == nums[j-1]` | same |
| Set membership | `if c in cols` | `if (cols.contains(c))` |

## 5. Common pitfalls

- **Forgetting to undo.** Every choice you make must be reversible.
- **Forgetting to copy when recording.** Most "find all" problems need
  `path.copy()` (or `new ArrayList<>(path)`) — a reference would mutate
  as you backtrack.
- **Off-by-one in the duplicate-skip.** The check
  `j > i and nums[j] == nums[j-1]` works because we always enter the
  loop at `i` with sorted `nums`. The "first" iteration at each depth
  is the one that starts the new branch.
- **Substring / list-copy cost.** For long paths, the `copy()` is the
  bottleneck; for n ≤ 16 it's fine.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

backtracking · state-space tree · include/skip · row-by-row ·
duplicate-skip · undo

**Next →** [Module 11: Graphs](../11-graphs/)
