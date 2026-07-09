# Validate Binary Search Tree

**Difficulty:** Medium

## Problem

Given the `root` of a binary tree, determine if it is a valid binary search tree (BST). A valid BST is defined as follows: the left subtree of a node contains only nodes with keys **less than** the node's key; the right subtree of a node contains only nodes with keys **greater than** the node's key; both the left and right subtrees must also be binary search trees.

## Examples

```
Input:  root = [2,1,3]
Output: True
```

```
Input:  root = [5,1,4,null,null,3,6]
Output: False
```

## Constraints

- 1 <= number of nodes <= 10^4
- -2^31 <= Node.val <= 2^31 - 1

## Hints

1. Don't just check `left.val < node.val < right.val` — that misses violations deeper in the tree.
2. Pass a (lo, hi) range down. Each node must lie in its range.

## Solution

See [`../../solutions/07-validate-binary-search-tree/`](../../solutions/07-validate-binary-search-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.
