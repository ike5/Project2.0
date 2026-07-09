# Binary Tree Right Side View

**Difficulty:** Medium

## Problem

Given the `root` of a binary tree, imagine yourself standing on the right side of it, return the values of the nodes you can see ordered from top to bottom.

## Examples

```
Input:  root = [1,2,3,null,5,null,4]
Output: [1,3,4]
```

```
Input:  root = [1,null,3]
Output: [1,3]
```

## Constraints

- 0 <= number of nodes <= 100
- -100 <= Node.val <= 100

## Hints

1. BFS: take the last element of each level.
2. Or: DFS, going right first; record each new depth's first node.

## Solution

See [`../../solutions/11-binary-tree-right-side-view/`](../../solutions/11-binary-tree-right-side-view/) for the Python and Java 21 solutions and a step-by-step walkthrough.
