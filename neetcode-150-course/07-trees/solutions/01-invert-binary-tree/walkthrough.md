# Invert Binary Tree - walkthrough

**Difficulty:** Easy &middot; **Module:** 07 Trees

## Brief

Given the `root` of a binary tree, invert the tree, and return its root.

## Examples

- `root = [4,2,7,1,3,6,9]` &rarr; `[4,7,2,9,6,3,1]`
- `root = [2,1,3]` &rarr; `[2,3,1]`

## Constraints

- 0 <= number of nodes <= 100
- -100 <= Node.val <= 100

## Intuition

Recursive swap. The base case is the empty tree.

**Time:** O(n). **Space:** O(h) for the recursion stack.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
