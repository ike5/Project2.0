# Module 14 — Intervals & Bit Manipulation 🔢

**Goal:** solve interval-merge and matrix-rotation problems; master
bitwise tricks. ⏱️ ~4 h · 🎯 Prereq: 13.

```
intervals: sort by start or end, then sweep
bit tricks: AND, OR, XOR, <<, >> — the right tool for "lowest common ancestor of bit patterns"
```

---

## 1. Intervals

The "intervals" family of problems has two flavors:

- **Sort by start, then merge** (Merge Intervals, Insert Interval).
- **Sort by end, then greedily keep** (Non-Overlapping Intervals,
  Meeting Rooms).

Sort is the workhorse. O(n log n) for the sort, O(n) for the sweep.

## 2. Matrix rotations and spirals

A 90° clockwise rotation is a **transpose** + **reverse each row**.
Spiral order is "walk the four edges, shrink the rectangle."

In-place matrix tricks:
- **Set Matrix Zeroes**: use the first row and column as flags.
- **Rotate Image**: transpose + reverse.
- **Spiral Matrix**: four boundaries.

## 3. Bit manipulation basics

| Operation | Python | Java |
|-----------|--------|------|
| AND | `a & b` | `a & b` |
| OR | `a \| b` | `a \| b` |
| XOR | `a ^ b` | `a ^ b` |
| NOT | `~a` | `~a` |
| Left shift | `a << k` | `a << k` |
| Right shift (signed) | `a >> k` | `a >> k` |
| Right shift (unsigned) | (n/a) | `a >>> k` |
| Popcount | `bin(a).count('1')` | `Integer.bitCount(a)` |
| Lowest set bit | `a & -a` | `a & -a` |

> **In Java, watch out for `>>>` vs `>>`.** Use `>>>` for unsigned shift
> when working with bitwise ranges (especially when the high bit could
> become 1).

## 4. The 8 problems

| #  | Problem | Difficulty | Idea |
|----|---------|-----------|------|
| 01 | [Insert Interval](./problems/01-insert-interval/) | Medium | Three sections, merge middle |
| 02 | [Merge Intervals](./problems/02-merge-intervals/) | Medium | Sort by start, sweep |
| 03 | [Non-Overlapping Intervals](./problems/03-non-overlapping-intervals/) | Medium | Sort by end, greedy keep |
| 04 | [Meeting Rooms II](./problems/04-meeting-rooms-ii/) | Medium | Sort starts & ends, sweep |
| 05 | [Rotate Image](./problems/05-rotate-image/) | Medium | Transpose + reverse |
| 06 | [Spiral Matrix](./problems/06-spiral-matrix/) | Medium | Four boundaries |
| 07 | [Set Matrix Zeroes](./problems/07-set-matrix-zeroes/) | Medium | First row/column as flags |
| 08 | [Bitwise AND of Numbers Range](./problems/08-bitwise-and-of-numbers-range/) | Medium | Common bit prefix |

## 5. Common pitfalls

- **Off-by-one in interval boundaries.** "Inclusive" vs "exclusive"
  affects whether two touching intervals overlap.
- **`>>` vs `>>>` in Java.** A negative number with `>>` stays negative
  (sign extension). Use `>>>` for the bit trick.
- **In-place matrix mutations.** Be careful about the order: zeroing
  the first row before recording whether it needs to be zeroed loses
  information.
- **The "common prefix" trick in `Bitwise AND of Numbers Range` only
  works because once a bit flips, the AND of all numbers in any range
  including both ends is 0 in that position.**

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

interval sort · sweep · greedy by end · matrix transpose ·
spiral · bitwise AND · common prefix

🎉 **You've finished the NeetCode 150!**
