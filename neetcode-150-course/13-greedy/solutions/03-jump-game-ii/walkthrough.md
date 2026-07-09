# Jump Game II - walkthrough

**Difficulty:** Medium &middot; **Module:** 13 Greedy

## Brief

You are given a **0-indexed** array of integers `nums` of length `n`. You are initially positioned at `nums[0]`. Each element `nums[i]` represents the maximum jump length from that index. Return the minimum number of jumps to reach `nums[n - 1]`. The test cases are generated such that you can reach `nums[n - 1]`.

## Examples

- `nums = [2,3,1,1,4]` &rarr; `2`
- `nums = [2,3,0,1,4]` &rarr; `2`

## Constraints

- 1 <= len(nums) <= 10^4
- 0 <= nums[i] <= 1000
- It's always possible to reach the end

## Intuition

Greedy BFS. `cur_end` is the end of the current jump's reach;
when we hit it, take another jump and extend the window.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
