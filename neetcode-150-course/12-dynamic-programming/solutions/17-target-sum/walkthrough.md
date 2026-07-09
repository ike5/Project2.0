# Target Sum - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

You are given an integer array `nums` and an integer `target`. You want to build an expression by placing a `+` or `-` sign in front of each integer in `nums` and then concatenate all the signed integers. Return the number of different expressions that you can build, which evaluate to `target`.

## Examples

- `nums = [1,1,1,1,1], target = 3` &rarr; `5`
- `nums = [1], target = 1` &rarr; `1`

## Constraints

- 1 <= nums.length <= 20
- 0 <= nums[i] <= 1000
- 0 <= sum(nums[i]) <= 1000
- -1000 <= target <= 1000

## Intuition

Let `P` be the sum of positive-signed numbers, `N` negative.
`P - N = target` and `P + N = total`, so `P = (total + target) / 2`.
Count subsets summing to `P`.

**Time:** O(n · total). **Space:** O(total).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
