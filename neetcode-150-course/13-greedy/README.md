# Module 13 — Greedy 💰

**Goal:** make locally optimal choices that turn out to be globally
optimal. ⏱️ ~4 h · 🎯 Prereq: 12.

```
greedy: pick the locally best move; works when choices compose to a global optimum
```

---

## 1. When is greedy correct?

A greedy algorithm is correct when the locally optimal choice is *also*
part of a globally optimal solution. The four most common conditions:

- **Greedy choice property**: a local optimum is contained in a global
  optimum.
- **Optimal substructure**: an optimal solution to the whole problem
  contains optimal solutions to sub-problems.
- **Exchange argument**: if an optimal solution doesn't pick the
  greedy choice, you can swap it in and not make things worse.
- **Monotonicity**: pushing a "high water mark" further is always
  better (Jump Game, Gas Station).

If you can't prove one of these, you usually need DP.

## 2. The 8 problems — easy → hard

| #  | Problem | Difficulty | Idea |
|----|---------|-----------|------|
| 01 | [Maximum Subarray](./problems/01-maximum-subarray/) | Easy | Kadane's |
| 02 | [Jump Game](./problems/02-jump-game/) | Medium | Farthest reachable |
| 03 | [Jump Game II](./problems/03-jump-game-ii/) | Medium | Greedy BFS |
| 04 | [Gas Station](./problems/04-gas-station/) | Medium | Reset on dip |
| 05 | [Hand of Straights](./problems/05-hand-of-straights/) | Medium | Form groups from smallest |
| 06 | [Merge Triplets to Form Target](./problems/06-merge-triplets-to-form-target/) | Medium | Greedy max of valid |
| 07 | [Partition Labels](./problems/07-partition-labels/) | Medium | Last-occurrence |
| 08 | [Valid Parenthesis String](./problems/08-valid-parenthesis-string/) | Medium | Range of open counts |

## 3. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Heap of size k | `heapq` | `PriorityQueue` |
| `Counter` | `collections.Counter` | `Map<K,Integer>` + `merge` |
| Sorted iteration | `sorted(cnt)` | `TreeMap` or `new int[26]` |
| Char to int | `ord(c) - ord('a')` | `c - 'a'` |
| Compare lists | `==` | `Arrays.equals` |
| List comp | `[x for x in xs]` | `List<Integer> out = new ArrayList<>(); for (...) out.add(...);` |

## 4. Common pitfalls

- **"Greedy is wrong" proofs.** If you can't prove a greedy is correct,
  it isn't. Try a counter-example.
- **Off-by-one in the range.** "Low" must be clamped to 0 (`max(lo-1, 0)`).
- **Reset vs continue.** In Gas Station, the *first* station that fails
  isn't the start, but the next one might be.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

greedy choice property · optimal substructure · exchange argument ·
Kadane's algorithm · gas station reset · range DP

**Next →** [Module 14: Intervals & Bit Manipulation](../14-intervals-bit-manipulation/)
