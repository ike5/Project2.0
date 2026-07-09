# Course Schedule

**Difficulty:** Medium

## Problem

There are a total of `numCourses` courses you have to take, labeled from `0` to `numCourses - 1`. You are given an array `prerequisites` where `prerequisites[i] = [ai, bi]` indicates that you must take course `bi` first if you want to take course `ai`. Return `True` if you can finish all courses. Otherwise, return `False`.

## Examples

```
Input:  numCourses = 2, prerequisites = [[1,0]]
Output: True
```

```
Input:  numCourses = 2, prerequisites = [[1,0],[0,1]]
Output: False
```

## Constraints

- 1 <= numCourses <= 2000
- 0 <= prerequisites.length <= 5000
- prerequisites[i].length == 2
- 0 <= ai, bi < numCourses
- All the pairs prerequisites[i] are unique

## Hints

1. Detect a cycle in the directed graph of prerequisites.

## Solution

See [`../../solutions/08-course-schedule/`](../../solutions/08-course-schedule/) for the Python and Java 21 solutions and a step-by-step walkthrough.
