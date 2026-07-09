# Subtree of Another Tree

**Difficulty:** Easy

## Problem

Given the roots of two binary trees `root` and `subRoot`, return `True` if there is a subtree of `root` with the same structure and node values of `subRoot` and `False` otherwise.

## Examples

```
Input:  root = [3,4,5,1,2], subRoot = [4,1,2]
Output: True
```

```
Input:  root = [3,4,5,1,2,null,null,null,null,0], subRoot = [4,1,2]
Output: False
```

## Constraints

- 0 <= number of nodes <= 2000
- -10^4 <= Node.val <= 10^4

## Hints

1. For each node in `root`, check if the subtree rooted there equals `subRoot`.
2. Faster with KMP / hash, but the O(n*m) version is fine for interviews.

## Solution

See [`../../solutions/04-subtree-of-another-tree/`](../../solutions/04-subtree-of-another-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.
