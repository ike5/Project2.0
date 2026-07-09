# Subtree of Another Tree - walkthrough

**Difficulty:** Easy &middot; **Module:** 07 Trees

## Brief

Given the roots of two binary trees `root` and `subRoot`, return `True` if there is a subtree of `root` with the same structure and node values of `subRoot` and `False` otherwise.

## Examples

- `root = [3,4,5,1,2], subRoot = [4,1,2]` &rarr; `True`
- `root = [3,4,5,1,2,null,null,null,null,0], subRoot = [4,1,2]` &rarr; `False`

## Constraints

- 0 <= number of nodes <= 2000
- -10^4 <= Node.val <= 10^4

## Intuition

Walk `root`; at each node, check if the subtree rooted there equals
`subRoot`. If so, return true. Otherwise recurse.

**Time:** O(n · m) in the worst case. **Space:** O(h).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
