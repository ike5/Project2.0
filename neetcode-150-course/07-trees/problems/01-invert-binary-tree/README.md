# Invert Binary Tree

**Difficulty:** Easy

## Problem

Given the `root` of a binary tree, invert the tree, and return its root.

## Examples

```
Input:  root = [4,2,7,1,3,6,9]
Output: [4,7,2,9,6,3,1]
```

```
Input:  root = [2,1,3]
Output: [2,3,1]
```

## Constraints

- 0 <= number of nodes <= 100
- -100 <= Node.val <= 100

## Hints

1. Recursive: swap each node's left and right, recurse on both.

## Solution

See [`../../solutions/01-invert-binary-tree/`](../../solutions/01-invert-binary-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.
