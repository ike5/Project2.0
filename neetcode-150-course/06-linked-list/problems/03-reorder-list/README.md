# Reorder List

**Difficulty:** Medium

## Problem

You are given the head of a singly linked list. Reorder the list to be: `L0 → L1 → … → Ln-1 → Ln` becomes `L0 → Ln → L1 → Ln-1 → L2 → Ln-2 → …`. You may not modify the values in the list's nodes, only nodes themselves may be changed.

## Examples

```
Input:  head = [1,2,3,4]
Output: [1,4,2,3]
```

```
Input:  head = [1,2,3,4,5]
Output: [1,5,2,4,3]
```

## Constraints

- 1 <= number of nodes <= 5 * 10^4
- 1 <= Node.val <= 1000

## Hints

1. Find the middle (slow/fast), reverse the second half, then interleave the two halves.

## Solution

See [`../../solutions/03-reorder-list/`](../../solutions/03-reorder-list/) for the Python and Java 21 solutions and a step-by-step walkthrough.
