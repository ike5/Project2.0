# Binary Tree Maximum Path Sum

**Difficulty:** Hard

## Problem

A **path** in a binary tree is a sequence of nodes where each pair of adjacent nodes in the sequence has an edge connecting them. A node can only appear in the sequence at most once. Note that the path does not need to pass through the root. The **path sum** of a path is the sum of the node's values in the path. Given the `root` of a binary tree, return the maximum path sum of any **non-empty** path.

## Examples

```
Input:  root = [1,2,3]
Output: 6
```

```
Input:  root = [-10,9,20,null,null,15,7]
Output: 42
```

## Constraints

- 1 <= number of nodes <= 3 * 10^4
- -1000 <= Node.val <= 1000

## Hints

1. For each node, compute the best 'path through this node'. Update global max.
2. Return the best 'single-branch' path going up (so the parent can use us as a side).

## Solution

See [`../../solutions/15-binary-tree-maximum-path-sum/`](../../solutions/15-binary-tree-maximum-path-sum/) for the Python and Java 21 solutions and a step-by-step walkthrough.
