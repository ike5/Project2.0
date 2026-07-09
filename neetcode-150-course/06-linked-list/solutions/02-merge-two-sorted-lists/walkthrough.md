# Merge Two Sorted Lists - walkthrough

**Difficulty:** Easy &middot; **Module:** 06 Linked List

## Brief

You are given the heads of two sorted linked lists `list1` and `list2`. Merge the two lists into one **sorted** list and return its head. The list should be made by splicing together the nodes of the first two lists.

## Examples

- `list1 = [1,2,4], list2 = [1,3,4]` &rarr; `[1,1,2,3,4,4]`
- `list1 = [], list2 = []` &rarr; `[]`
- `list1 = [], list2 = [0]` &rarr; `[0]`

## Constraints

- 0 <= number of nodes in each list <= 50
- -100 <= Node.val <= 100
- Both lists are sorted in non-decreasing order

## Intuition

Use a **dummy head** so we don't have to special-case the first
node. The dummy is a sentinel; the real result starts at `dummy.next`.

**Time:** O(n + m). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
