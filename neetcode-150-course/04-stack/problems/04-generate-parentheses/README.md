# Generate Parentheses

**Difficulty:** Medium

## Problem

Given `n` pairs of parentheses, write a function to generate all combinations of well-formed parentheses.

## Examples

```
Input:  n = 3
Output: ['((()))','(()())','(())()','()(())','()()()']
```

```
Input:  n = 1
Output: ['()']
```

## Constraints

- 1 <= n <= 8

## Hints

1. Backtrack: add '(' if we still have openers; add ')' if we have more opens than closes so far.
2. Stop when the string has length 2n.

## Solution

See [`../../solutions/04-generate-parentheses/`](../../solutions/04-generate-parentheses/) for the Python and Java 21 solutions and a step-by-step walkthrough.
