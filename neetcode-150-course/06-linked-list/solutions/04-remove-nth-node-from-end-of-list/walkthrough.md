# Remove Nth Node From End of List - walkthrough

**Difficulty:** Medium &middot; **Module:** 06 Linked List

## Brief

Given the `head` of a linked list, remove the `n`th node from the end of the list and return its head.

## Examples

- `head = [1,2,3,4,5], n = 2` &rarr; `[1,2,3,5]`
- `head = [1], n = 1` &rarr; `[]`
- `head = [1,2], n = 1` &rarr; `[1]`

## Constraints

- 1 <= number of nodes <= 30
- 1 <= n <= number of nodes

## Intuition

Use a **dummy head** so removing the first node is the same as
removing any other. Walk `fast` ahead by `n`, then walk both pointers
together; when `fast` hits the end, `slow` is just before the target.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
