# Longest Consecutive Sequence - walkthrough

**Difficulty:** Medium &middot; **Module:** 01 Arrays Hashing

## Brief

Given an unsorted array of integers `nums`, return the length of the longest sequence of consecutive elements. The algorithm must run in O(n) time.

## Examples

- `nums = [100,4,200,1,3,2]` &rarr; `4`
- `nums = [0,3,7,2,5,8,4,6,0,1]` &rarr; `9`
- `nums = []` &rarr; `0`

## Constraints

- 0 <= nums.length <= 10^5
- -10^9 <= nums[i] <= 10^9

## Intuition

For each `x`, ask: is `x-1` also in the array? If **no**, then `x` is the
*start* of a run, and we walk forward counting how long the run is.

This guarantees each element is visited at most twice (once as the outer
loop, at most once as `x + length` for some other start), so the total work
is O(n).

## Approach
1. Put everything in a set.
2. For each `x` in the set:
   - If `x - 1` is in the set, skip — we don't want to start in the middle.
   - Otherwise, walk `x + 1, x + 2, ...` while present, counting.
3. Return the longest count.

## Complexity
- **Time:** O(n) — each element is checked O(1) times in the outer loop and
  O(1) times in the inner walk (since it can only be `x + length` for a
  single start).
- **Space:** O(n) for the set.

## Follow-ups
- *What if you can sort?* Sort in O(n log n), then walk adjacent pairs.
  Easier to code, but slower.
- *Streaming input?* Maintain a `Map<Integer, Integer>` of "run length ending
  at x" using Union-Find-like merging. (Module 11.)

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
