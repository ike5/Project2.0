# Number of Connected Components in an Undirected Graph - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

You have a graph of `n` nodes labeled from `0` to `n - 1`. You are given an integer `n` and an array `edges` where `edges[i] = [ai, bi]` indicates that there is an edge between `ai` and `bi` in the graph. Return the number of connected components in the graph.

## Examples

- `n = 5, edges = [[0,1],[1,2],[3,4]]` &rarr; `2`
- `n = 5, edges = [[0,1],[1,2],[2,3],[3,4]]` &rarr; `1`

## Constraints

- 1 <= n <= 2000
- 0 <= edges.length <= n * (n - 1) / 2

## Intuition

Union-Find. Each edge unites two components. The number of
distinct roots at the end is the answer.

**Time:** O(V + E · α(V)). **Space:** O(V).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
