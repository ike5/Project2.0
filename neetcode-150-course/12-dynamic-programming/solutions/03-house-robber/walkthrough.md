# House Robber - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

You are a professional robber planning to rob houses along a street. Each house has a certain amount of money stashed, the only constraint stopping you from robbing each of them is that adjacent houses have security systems connected and **it will automatically contact the police if two adjacent houses were broken into on the same night**. Given an integer array `nums` representing the amount of money at each house, return the maximum amount of money you can rob tonight **without alerting the police**.

## Examples

- `nums = [1,2,3,1]` &rarr; `4`
- `nums = [2,7,9,3,1]` &rarr; `12`

## Constraints

- 1 <= nums.length <= 100
- 0 <= nums[i] <= 400

## Intuition

Standard 1D DP. Two rolling variables: `a` = best through `i-2`,
`b` = best through `i-1`.

**Time:** O(n). **Space:** O(1).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
