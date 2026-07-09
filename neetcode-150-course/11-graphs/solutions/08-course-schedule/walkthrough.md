# Course Schedule - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

There are a total of `numCourses` courses you have to take, labeled from `0` to `numCourses - 1`. You are given an array `prerequisites` where `prerequisites[i] = [ai, bi]` indicates that you must take course `bi` first if you want to take course `ai`. Return `True` if you can finish all courses. Otherwise, return `False`.

## Examples

- `numCourses = 2, prerequisites = [[1,0]]` &rarr; `True`
- `numCourses = 2, prerequisites = [[1,0],[0,1]]` &rarr; `False`

## Constraints

- 1 <= numCourses <= 2000
- 0 <= prerequisites.length <= 5000
- prerequisites[i].length == 2
- 0 <= ai, bi < numCourses
- All the pairs prerequisites[i] are unique

## Intuition

Kahn's algorithm (topological sort via BFS). If we can take all
courses, there's no cycle. Count how many we actually took.

**Time:** O(V + E). **Space:** O(V + E).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
