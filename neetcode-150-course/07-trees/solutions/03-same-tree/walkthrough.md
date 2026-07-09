# Same Tree - walkthrough

**Difficulty:** Easy &middot; **Module:** 07 Trees

## Brief

Given the roots of two binary trees `p` and `q`, write a function to check if they are the same or not. Two binary trees are considered the same if they are structurally identical, and the nodes have the same value.

## Examples

- `p = [1,2,3], q = [1,2,3]` &rarr; `True`
- `p = [1,2], q = [1,null,2]` &rarr; `False`

## Constraints

- 0 <= number of nodes <= 100
- -10^4 <= Node.val <= 10^4

## Intuition

Recursive equality on both subtrees.

**Time:** O(min(n, m)). **Space:** O(h).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
