# Redundant Connection - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

In this problem, a tree is an undirected graph that is connected and has no cycles. You are given a graph that started as a tree with `n` nodes labeled from `1` to `n`, with one additional edge added. The added edge has two different vertices chosen from `1` to `n`, and was not an edge that already existed. The graph is represented as an array `edges` of length `n` where `edges[i] = [ai, bi]` indicates that there is an edge between nodes `ai` and `bi` in the graph. Return an edge that can be removed so that the resulting graph is a tree with `n` nodes. If there are multiple answers, return the edge that appears **last** in the input.

## Examples

- `edges = [[1,2],[1,3],[2,3]]` &rarr; `[2, 3]`
- `edges = [[1,2],[2,3],[3,4],[1,4],[1,5]]` &rarr; `[1, 4]`

## Constraints

- n == edges.length
- 3 <= n <= 1000
- edges[i].length == 2
- 1 <= ai < bi <= edges.length
- There are no repeated edges
- The given graph is connected

## Intuition

Union-Find. The first edge whose endpoints are already in the
same component creates a cycle — that's the redundant edge.

**Time:** O(n · α(n)). **Space:** O(n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
