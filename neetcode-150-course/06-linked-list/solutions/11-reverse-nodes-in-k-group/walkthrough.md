# Reverse Nodes in k-Group - walkthrough

**Difficulty:** Hard &middot; **Module:** 06 Linked List

## Brief

Given the `head` of a linked list, reverse the nodes of the list `k` at a time, and return the modified list. `k` is a positive integer. If the number of nodes is not a multiple of `k`, the remaining nodes at the end should stay in the same order.

## Examples

- `head = [1,2,3,4,5], k = 2` &rarr; `[2,1,4,3,5]`
- `head = [1,2,3,4,5], k = 3` &rarr; `[3,2,1,4,5]`

## Constraints

- 1 <= k <= number of nodes
- 0 <= number of nodes <= 5000
- 0 <= Node.val <= 1000

## Intuition

Iterate in groups of `k`. For each group:

1. Walk `k` steps from `groupPrev` to find the end of the group; if you
   run out, the remaining nodes don't get reversed.
2. Reverse the group in place.
3. Reconnect: the previous group's tail now points to the new head; the
   old head (now the new tail) points to the next group.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
