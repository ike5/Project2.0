# Graph Valid Tree

**Difficulty:** Medium

## Problem

You have a graph of `n` nodes labeled from `0` to `n - 1`. You are given an integer `n` and a list of `edges` where `edges[i] = [ai, bi]` indicates that there is an undirected edge between nodes `ai` and `bi` in the graph. Return `True` if the edges of the given graph make up a valid tree, and `False` otherwise.

## Examples

```
Input:  n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]
Output: True
```

```
Input:  n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]
Output: False
```

## Constraints

- 1 <= n <= 2000
- 0 <= edges.length <= n * (n - 1) / 2

## Hints

1. A graph is a tree iff (a) it has exactly n-1 edges and (b) it's connected.

## Solution

See [`../../solutions/10-graph-valid-tree/`](../../solutions/10-graph-valid-tree/) for the Python and Java 21 solutions and a step-by-step walkthrough.
