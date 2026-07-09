# Module 12 — Dynamic Programming 🧮

**Goal:** turn recursive structure into iterative DP. ⏱️ ~14 h · 🎯
Prereq: 11.

```
DP: subproblems → recurrence → memoize (top-down) or tabulate (bottom-up)
```

---

## 1. The DP recipe

1. Define the state: `dp[i]` or `dp[i][j]` = "answer for subproblem".
2. Recurrence: how does the answer for `i` depend on smaller states?
3. Base cases: smallest subproblems.
4. Order: process in a sequence that respects the recurrence.
5. Optimize: roll to 1D when possible, or use `O(1)` space.

## 2. Top-down vs bottom-up

| Style | When |
|-------|------|
| **Top-down** (memoized recursion) | Easier to write, but recursion overhead. |
| **Bottom-up** (iterative table) | Faster in practice; required when stack depth is a concern. |

In Python, top-down is often clearer. In Java, bottom-up is more common.

## 3. The 22 problems — easy → hard

This is the largest module. Below are the canonical NeetCode 150 DP
problems, ordered easy → hard. Each one introduces a recurring pattern.

| # | Problem | Diff | Pattern |
|---|---------|------|---------|
| 01 | [Climbing Stairs](./problems/01-climbing-stairs/) | E | 1D Fibonacci |
| 02 | [Min Cost Climbing Stairs](./problems/02-min-cost-climbing-stairs/) | E | 1D Fibonacci with cost |
| 03 | [House Robber](./problems/03-house-robber/) | M | Rob/skip |
| 04 | [House Robber II](./problems/04-house-robber-ii/) | M | Rob/skip, two cases |
| 05 | [Longest Palindromic Substring](./problems/05-longest-palindromic-substring/) | M | Expand around center |
| 06 | [Palindromic Substrings](./problems/06-palindromic-substrings/) | M | Expand + count |
| 07 | [Decode Ways](./problems/07-decode-ways/) | M | 1D, 1- and 2-digit |
| 08 | [Coin Change](./problems/08-coin-change/) | M | Unbounded knapsack |
| 09 | [Maximum Product Subarray](./problems/09-maximum-product-subarray/) | M | Track min and max |
| 10 | [Word Break](./problems/10-word-break/) | M | Subset + dict |
| 11 | [Longest Increasing Subsequence](./problems/11-longest-increasing-subsequence/) | M | Patience sorting O(n log n) |
| 12 | [Partition Equal Subset Sum](./problems/12-partition-equal-subset-sum/) | M | 0/1 knapsack |
| 13 | [Unique Paths](./problems/13-unique-paths/) | M | 2D grid, 1D rolling |
| 14 | [Longest Common Subsequence](./problems/14-longest-common-subsequence/) | M | 2D string DP, 1D rolling |
| 15 | [Best Time to Buy and Sell Stock with Cooldown](./problems/15-best-time-to-buy-and-sell-stock-with-cooldown/) | M | State machine |
| 16 | [Coin Change II](./problems/16-coin-change-ii/) | M | Unbounded knapsack count |
| 17 | [Target Sum](./problems/17-target-sum/) | M | Subset sum reduce |
| 18 | [Interleaving String](./problems/18-interleaving-string/) | M | 2D interleaving |
| 19 | [Edit Distance](./problems/19-edit-distance/) | M | 2D string DP |
| 20 | [Best Time to Buy and Sell Stock III](./problems/20-best-time-to-buy-and-sell-stock-iii/) | H | 4-state DP |
| 21 | [Best Time to Buy and Sell Stock IV](./problems/21-best-time-to-buy-and-sell-stock-iv/) | H | K-state DP |
| 22 | [Maximal Square](./problems/22-maximal-square/) | H | 2D grid, side length |

## 4. Common pitfalls

- **Off-by-one in the recurrence.** Is `dp[i]` the answer *up to* `i` or
  *ending at* `i`? Pick one and stick with it.
- **Rolling variable management.** In 1D rolling, you often need a
  `prev` (the `dp[i-1][j-1]` from the previous row). Don't lose it.
- **Knapsack direction.** For 0/1 knapsack, iterate the inner loop
  **backwards** to avoid using the same item twice.
- **State explosion.** Stock problems with k transactions have O(k)
  states; don't add a `transaction_count` dimension to the array.
- **Stale `prev`.** In a one-row rolling update, `prev` must be set
  *before* the current cell is overwritten.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

state · recurrence · base case · memoization · tabulation · rolling
array · 0/1 knapsack · unbounded knapsack · patience sorting

**Next →** [Module 13: Greedy](../13-greedy/)
