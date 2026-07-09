# Merge K Sorted Lists - walkthrough

**Difficulty:** Hard &middot; **Module:** 06 Linked List

## Brief

You are given an array of `k` linked lists, each sorted in ascending order. Merge all the linked lists into one sorted linked list and return it.

## Examples

- `lists = [[1,4,5],[1,3,4],[2,6]]` &rarr; `[1,1,2,3,4,4,5,6]`
- `lists = []` &rarr; `[]`
- `lists = [[]]` &rarr; `[]`

## Constraints

- 0 <= k <= 10^4
- 0 <= lists[i].length <= 500
- -10^4 <= lists[i][j] <= 10^4
- lists[i] is sorted in ascending order
- The total number of nodes won't exceed 10^4

## Intuition

**Min-heap of size k.** Push the head of each non-empty list. Each
step: pop the smallest head, append it to the result, and push its
`next` (if any).

**Time:** O(N log k) where N is the total number of nodes.
**Space:** O(k) for the heap.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
