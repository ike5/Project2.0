# Binary Tree Right Side View - walkthrough

**Difficulty:** Medium &middot; **Module:** 07 Trees

## Brief

Given the `root` of a binary tree, imagine yourself standing on the right side of it, return the values of the nodes you can see ordered from top to bottom.

## Examples

- `root = [1,2,3,null,5,null,4]` &rarr; `[1,3,4]`
- `root = [1,null,3]` &rarr; `[1,3]`

## Constraints

- 0 <= number of nodes <= 100
- -100 <= Node.val <= 100

## Intuition

BFS: at each level, the last node is the rightmost. Record it.

**Time:** O(n). **Space:** O(w).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
