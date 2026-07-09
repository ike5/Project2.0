# Maximum Depth of Binary Tree

**Difficulty:** Easy

## Problem

Given the `root` of a binary tree, return its maximum depth. A binary tree's maximum depth is the number of nodes along the longest path from the root node down to the farthest leaf node.

## Examples

```
Input:  root = [3,9,20,null,null,15,7]
Output: 3
```

```
Input:  root = [1,null,2]
Output: 2
```

## Constraints

- 0 <= number of nodes <= 10^4
- -100 <= Node.val <= 100

## Hints

1. Recursive: 1 + max(depth(left), depth(right)).
2. Iterative: BFS, count levels.

## Solution

See [`../../solutions/02-maximum-depth-of-binary-tree/`](../../solutions/02-maximum-depth-of-binary-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.
