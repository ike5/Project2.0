# Generate Parentheses - walkthrough

**Difficulty:** Medium &middot; **Module:** 04 Stack

## Brief

Given `n` pairs of parentheses, write a function to generate all combinations of well-formed parentheses.

## Examples

- `n = 3` &rarr; `['((()))','(()())','(())()','()(())','()()()']`
- `n = 1` &rarr; `['()']`

## Constraints

- 1 <= n <= 8

## Intuition

Backtracking. Two counts: how many `'('` we've placed and how many
`')'`. We can place another `'('` if `opens < n`. We can place another
`')'` if `closes < opens` (otherwise the prefix would be unbalanced).

**Time:** O(4^n / sqrt(n)) — the Catalan number. **Space:** O(n) recursion
depth.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
