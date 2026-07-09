# Top K Frequent Elements

**Difficulty:** Medium

## Problem

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. You may return the answer in any order.

## Examples

```
Input:  nums = [1,1,1,2,2,3], k = 2
Output: [1, 2]
```

```
Input:  nums = [1], k = 1
Output: [1]
```

## Constraints

- 1 <= nums.length <= 10^5
- k is in the range [1, the number of unique elements]

## Hints

1. Approach 1: a min-heap of size k — O(n log k).
2. Approach 2 (bucket sort): the max frequency is at most n. Make a list of buckets indexed by frequency, then walk down.

## Solution

See [`../../solutions/05-top-k-frequent-elements/`](../../solutions/05-top-k-frequent-elements/) for the Python and Java 21 solutions and a step-by-step walkthrough.
