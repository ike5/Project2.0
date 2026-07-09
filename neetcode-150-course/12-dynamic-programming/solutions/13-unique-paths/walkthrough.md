# Unique Paths - walkthrough

**Difficulty:** Medium &middot; **Module:** 12 Dynamic Programming

## Brief

There is a robot on an `m x n` grid. The robot is initially located at the top-left corner (i.e., `grid[0][0]`). The robot tries to move to the bottom-right corner (i.e., `grid[m - 1][n - 1]`). The robot can only move either down or right at any point in time. Given the two integers `m` and `n`, return the number of possible unique paths that the robot can take to reach the bottom-right corner.

## Examples

- `m = 3, n = 7` &rarr; `28`
- `m = 3, n = 2` &rarr; `3`

## Constraints

- 1 <= m, n <= 100

## Intuition

`dp[i][j] = dp[i-1][j] + dp[i][j-1]`. We only need one row of
rolling state.

**Time:** O(m · n). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
