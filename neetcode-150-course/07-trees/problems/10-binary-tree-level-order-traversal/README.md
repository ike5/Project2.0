# Binary Tree Level Order Traversal

**Difficulty:** Medium

## Problem

Given the `root` of a binary tree, return the level order traversal of its nodes' values (i.e., from left to right, level by level).

## Examples

```
Input:  root = [3,9,20,null,null,15,7]
Output: [[3],[9,20],[15,7]]
```

```
Input:  root = [1]
Output: [[1]]
```

## Constraints

- 0 <= number of nodes <= 2000
- -1000 <= Node.val <= 1000

## Hints

1. BFS with a queue. Record the size at the start of each level.

## Solution

See [`../../solutions/10-binary-tree-level-order-traversal/`](../../solutions/10-binary-tree-level-order-traversal/) for the Python and Java 21 solutions and a step-by-step walkthrough.
