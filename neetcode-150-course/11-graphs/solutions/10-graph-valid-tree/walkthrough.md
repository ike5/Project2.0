# Graph Valid Tree - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

You have a graph of `n` nodes labeled from `0` to `n - 1`. You are given an integer `n` and a list of `edges` where `edges[i] = [ai, bi]` indicates that there is an undirected edge between nodes `ai` and `bi` in the graph. Return `True` if the edges of the given graph make up a valid tree, and `False` otherwise.

## Examples

- `n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]` &rarr; `True`
- `n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]` &rarr; `False`

## Constraints

- 1 <= n <= 2000
- 0 <= edges.length <= n * (n - 1) / 2

## Intuition

A graph is a tree iff (a) exactly n-1 edges and (b) no cycle.
Union-Find detects cycles as we add edges.

**Time:** O(V + E · α(V)). **Space:** O(V).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
