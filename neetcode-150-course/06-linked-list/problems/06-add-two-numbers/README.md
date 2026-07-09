# Add Two Numbers

**Difficulty:** Medium

## Problem

You are given two non-empty linked lists representing two non-negative integers. The digits are stored in **reverse order**, and each node contains a single digit. Add the two numbers and return the sum as a linked list.

## Examples

```
Input:  l1 = [2,4,3], l2 = [5,6,4]
Output: [7,0,8]
```

```
Input:  l1 = [0], l2 = [0]
Output: [0]
```

```
Input:  l1 = [9,9,9,9], l2 = [9,9,9,9,9,9,9]
Output: [8,9,9,0,0,0,1]
```

## Constraints

- 1 <= number of nodes <= 100
- 0 <= Node.val <= 9
- The numbers do not contain leading zeros (except the number 0 itself)

## Hints

1. Walk both lists with a carry. Each step: sum = a + b + carry.

## Solution

See [`../../solutions/06-add-two-numbers/`](../../solutions/06-add-two-numbers/) for the Python and Java 21 solutions and a step-by-step walkthrough.
