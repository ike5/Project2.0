# Daily Temperatures

**Difficulty:** Medium

## Problem

Given an array of integers `temperatures` representing daily temperatures, return an array `answer` such that `answer[i]` is the number of days you have to wait after the ith day to get a warmer temperature. If there is no future day with a warmer temperature, set `answer[i] = 0`.

## Examples

```
Input:  temperatures = [73,74,75,71,69,72,76,73]
Output: [1,1,4,2,1,1,0,0]
```

```
Input:  temperatures = [30,40,50,60]
Output: [1,1,1,0]
```

## Constraints

- 1 <= len(temperatures) <= 10^5
- 30 <= temperatures[i] <= 100

## Hints

1. Monotonic stack: store indices of days with decreasing temperatures.
2. When today's temp is higher than the top, the top is resolved.

## Solution

See [`../../solutions/05-daily-temperatures/`](../../solutions/05-daily-temperatures/) for the Python and Java 21 solutions and a step-by-step walkthrough.
