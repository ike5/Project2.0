# Reorder List - walkthrough

**Difficulty:** Medium &middot; **Module:** 06 Linked List

## Brief

You are given the head of a singly linked list. Reorder the list to be: `L0 → L1 → … → Ln-1 → Ln` becomes `L0 → Ln → L1 → Ln-1 → L2 → Ln-2 → …`. You may not modify the values in the list's nodes, only nodes themselves may be changed.

## Examples

- `head = [1,2,3,4]` &rarr; `[1,4,2,3]`
- `head = [1,2,3,4,5]` &rarr; `[1,5,2,4,3]`

## Constraints

- 1 <= number of nodes <= 5 * 10^4
- 1 <= Node.val <= 1000

## Intuition

Three steps:

1. **Find middle** with slow/fast pointers. Cut the list at the middle.
2. **Reverse the second half** (Module-01 trick).
3. **Interleave** the two halves: take one from the first, one from the
   second, repeat.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
