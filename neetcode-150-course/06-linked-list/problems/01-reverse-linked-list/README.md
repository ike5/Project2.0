# Reverse Linked List

**Difficulty:** Easy

## Problem

Given the `head` of a singly linked list, reverse the list, and return the reversed list.

## Examples

```
Input:  head = [1,2,3,4,5]
Output: [5,4,3,2,1]
```

```
Input:  head = [1,2]
Output: [2,1]
```

```
Input:  head = []
Output: []
```

## Constraints

- 0 <= number of nodes <= 5000
- -5000 <= Node.val <= 5000

## Hints

1. Iterative with three pointers: `prev`, `curr`, `next_temp`.
2. Or recursive — return the new head and reverse the rest in place.

## Solution

See [`../../solutions/01-reverse-linked-list/`](../../solutions/01-reverse-linked-list/) for the Python and Java 21 solutions and a step-by-step walkthrough.
