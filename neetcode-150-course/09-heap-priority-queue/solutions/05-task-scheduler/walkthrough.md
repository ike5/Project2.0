# Task Scheduler - walkthrough

**Difficulty:** Medium &middot; **Module:** 09 Heap Priority Queue

## Brief

You are given an array of CPU tasks, each labeled with a letter from A to Z, and a number `n`. Each interval, the CPU can execute a task or be idle. There must be at least `n` intervals between executions of the same task. Return the minimum number of intervals the CPU needs to finish all tasks.

## Examples

- `tasks = ['A','A','A','B','B','B'], n = 2` &rarr; `8`
- `tasks = ['A','A','A','B','B','B'], n = 0` &rarr; `6`

## Constraints

- 1 <= task.length <= 10^4
- tasks[i] is an uppercase English letter
- 0 <= n <= 100

## Intuition

The most-frequent task determines a skeleton: `max_freq - 1` gaps
of length `n + 1` (the task plus its cooldown slots). The remaining
tasks fit into those gaps. If there are more tasks than slots, the
answer is just `len(tasks)`.

**Time:** O(n). **Space:** O(26).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
