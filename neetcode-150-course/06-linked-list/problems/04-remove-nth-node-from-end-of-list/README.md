# Remove Nth Node From End of List

**Difficulty:** Medium

## Problem

Given the `head` of a linked list, remove the `n`th node from the end of the list and return its head.

## Examples

```
Input:  head = [1,2,3,4,5], n = 2
Output: [1,2,3,5]
```

```
Input:  head = [1], n = 1
Output: []
```

```
Input:  head = [1,2], n = 1
Output: [1]
```

## Constraints

- 1 <= number of nodes <= 30
- 1 <= n <= number of nodes

## Hints

1. Two pointers: advance `fast` by n first; then walk both until `fast` is null. `slow.next` is the node to remove.

## Solution

See [`../../solutions/04-remove-nth-node-from-end-of-list/`](../../solutions/04-remove-nth-node-from-end-of-list/) for the Python and Java 21 solutions and a step-by-step walkthrough.
