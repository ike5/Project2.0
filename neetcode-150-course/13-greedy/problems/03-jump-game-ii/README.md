# Jump Game II

**Difficulty:** Medium

## Problem

You are given a **0-indexed** array of integers `nums` of length `n`. You are initially positioned at `nums[0]`. Each element `nums[i]` represents the maximum jump length from that index. Return the minimum number of jumps to reach `nums[n - 1]`. The test cases are generated such that you can reach `nums[n - 1]`.

## Examples

```
Input:  nums = [2,3,1,1,4]
Output: 2
```

```
Input:  nums = [2,3,0,1,4]
Output: 2
```

## Constraints

- 1 <= len(nums) <= 10^4
- 0 <= nums[i] <= 1000
- It's always possible to reach the end

## Hints

1. Greedy BFS: expand the window of reachable positions. Each expansion is a jump.

## Solution

See [`../../solutions/03-jump-game-ii/`](../../solutions/03-jump-game-ii/) for the Python and Java 21 solutions and a step-by-step walkthrough.
