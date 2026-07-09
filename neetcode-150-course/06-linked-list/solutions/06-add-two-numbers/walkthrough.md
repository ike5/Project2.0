# Add Two Numbers - walkthrough

**Difficulty:** Medium &middot; **Module:** 06 Linked List

## Brief

You are given two non-empty linked lists representing two non-negative integers. The digits are stored in **reverse order**, and each node contains a single digit. Add the two numbers and return the sum as a linked list.

## Examples

- `l1 = [2,4,3], l2 = [5,6,4]` &rarr; `[7,0,8]`
- `l1 = [0], l2 = [0]` &rarr; `[0]`
- `l1 = [9,9,9,9], l2 = [9,9,9,9,9,9,9]` &rarr; `[8,9,9,0,0,0,1]`

## Constraints

- 1 <= number of nodes <= 100
- 0 <= Node.val <= 9
- The numbers do not contain leading zeros (except the number 0 itself)

## Intuition

Walk both lists with a carry. Use `divmod(s, 10)` in Python
(equivalent to `s / 10` and `s % 10` in Java). The condition
`l1 != null || l2 != null || carry != 0` handles lists of unequal
length and a final carry.

**Time:** O(max(n, m)). **Space:** O(max(n, m)) for the result.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
