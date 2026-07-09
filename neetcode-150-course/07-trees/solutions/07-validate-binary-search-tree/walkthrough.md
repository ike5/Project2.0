# Validate Binary Search Tree - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given the `root` of a binary tree, determine if it is a valid binary search tree (BST). A valid BST is defined as follows: the left subtree of a node contains only nodes with keys **less than** the node's key; the right subtree of a node contains only nodes with keys **greater than** the node's key; both the left and right subtrees must also be binary search trees.

## Examples

- `root = [2,1,3]` &rarr; `True`
- `root = [5,1,4,null,null,3,6]` &rarr; `False`

## Constraints

- 1 <= number of nodes <= 10^4
- -2^31 <= Node.val <= 2^31 - 1

## Intuition

Pass a `(lo, hi)` range down. Each node's value must be in `(lo,
hi)`. Children inherit the parent's range narrowed by the parent's value.

> **Java note:** use `long` for `lo, hi` so `Integer.MIN_VALUE /
> Integer.MAX_VALUE` (the initial range) work correctly.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
