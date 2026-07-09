# Binary Tree Level Order Traversal - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given the `root` of a binary tree, return the level order traversal of its nodes' values (i.e., from left to right, level by level).

## Examples

- `root = [3,9,20,null,null,15,7]` &rarr; `[[3],[9,20],[15,7]]`
- `root = [1]` &rarr; `[[1]]`

## Constraints

- 0 <= number of nodes <= 2000
- -1000 <= Node.val <= 1000

## Intuition

BFS. At each iteration, the queue contains *exactly* one level;
record its size, then drain it.

**Time:** O(n). **Space:** O(w) where w is the maximum level width.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
