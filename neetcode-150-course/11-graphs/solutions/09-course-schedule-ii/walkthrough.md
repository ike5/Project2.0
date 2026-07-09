# Course Schedule II - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

Same problem as Course Schedule, but return the ordering of courses you should take to finish all courses. If there are many valid answers, return **any** of them. If it's impossible, return an empty array.

## Examples

- `numCourses = 2, prerequisites = [[1,0]]` &rarr; `[0, 1]`
- `numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]` &rarr; `[0, 2, 1, 3] or [0, 1, 2, 3]`

## Constraints

- Same as Course Schedule

## Intuition

Same as Course Schedule, but record the order in which we pop
from the queue.

**Time:** O(V + E). **Space:** O(V + E).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
