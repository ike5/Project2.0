# Count Good Nodes in Binary Tree

**Difficulty:** Medium

## Problem

Given a binary tree `root`, a node `x` in the tree is named **good** if in the path from root to `x`, there are no nodes with a value greater than `x`'s. Return the number of good nodes in the binary tree.

## Examples

```
Input:  root = [3,1,4,3,null,1,5]
Output: 4
```

```
Input:  root = [3,3,null,4,2]
Output: 3
```

## Constraints

- 1 <= number of nodes <= 10^5
- -10^4 <= Node.val <= 10^4

## Hints

1. DFS: pass the max so far down. A node is good if its val >= max.

## Solution

See [`../../solutions/12-count-good-nodes-in-binary-tree/`](../../solutions/12-count-good-nodes-in-binary-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.
