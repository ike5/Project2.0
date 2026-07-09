# Top K Frequent Elements - walkthrough

**Difficulty:** Medium &middot; **Module:** 01 Arrays Hashing

## Brief

Given an integer array `nums` and an integer `k`, return the `k` most frequent elements. You may return the answer in any order.

## Examples

- `nums = [1,1,1,2,2,3], k = 2` &rarr; `[1, 2]`
- `nums = [1], k = 1` &rarr; `[1]`

## Constraints

- 1 <= nums.length <= 10^5
- k is in the range [1, the number of unique elements]

## Intuition

Count everything, then pick the top k. The classic "top-k" problem.

## Approach
We use **bucket sort by frequency**. The max frequency is at most `n`, so we
make a list of `n+1` buckets where `buckets[f]` holds all values with
frequency `f`. Walk from the highest frequency down and take `k` values.

## Complexity
- **Time:** O(n) — counting, bucketing, and walking down are all linear.
- **Space:** O(n) — the count map and the buckets.

## Alternative: min-heap of size k
Maintain a heap of size k, push `(frequency, value)`, pop the smallest when
the heap grows past k. O(n log k) time, O(k) space. Use this if `k` is much
smaller than `n` and the value range is huge.

## Follow-ups
- *In O(k log k) total?* Quickselect on `(frequency, value)` pairs.
- *Streaming values?* Count-Sketch / Misra-Gries for approximate top-k.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
