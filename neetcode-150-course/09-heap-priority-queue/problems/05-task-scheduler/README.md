# Task Scheduler

**Difficulty:** Medium

## Problem

You are given an array of CPU tasks, each labeled with a letter from A to Z, and a number `n`. Each interval, the CPU can execute a task or be idle. There must be at least `n` intervals between executions of the same task. Return the minimum number of intervals the CPU needs to finish all tasks.

## Examples

```
Input:  tasks = ['A','A','A','B','B','B'], n = 2
Output: 8
```

```
Input:  tasks = ['A','A','A','B','B','B'], n = 0
Output: 6
```

## Constraints

- 1 <= task.length <= 10^4
- tasks[i] is an uppercase English letter
- 0 <= n <= 100

## Hints

1. Count frequencies. The most-frequent task sets the lower bound.
2. Answer = max(len(tasks), (max_freq - 1) * (n + 1) + count_max).

## Solution

See [`../../solutions/05-task-scheduler/`](../../solutions/05-task-scheduler/) for the Python and Java 21 solutions and a step-by-step walkthrough.
