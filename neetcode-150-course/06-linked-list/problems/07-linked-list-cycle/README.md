# Linked List Cycle

**Difficulty:** Easy

## Problem

Given `head`, the head of a linked list, determine if the linked list has a cycle in it. Return `True` if there is a cycle, `False` otherwise.

## Examples

```
Input:  head = [3,2,0,-4], pos = 1 (cycle back to index 1)
Output: True
```

```
Input:  head = [1,2], pos = -1 (no cycle)
Output: False
```

## Constraints

- 0 <= number of nodes <= 10^4
- -10^5 <= Node.val <= 10^5
- pos is -1 or a valid index

## Hints

1. Floyd's cycle finding: slow and fast pointers.
2. If they ever meet, there's a cycle. O(1) space.

## Solution

See [`../../solutions/07-linked-list-cycle/`](../../solutions/07-linked-list-cycle/) for the Python and Java 21 solutions and a step-by-step walkthrough.
