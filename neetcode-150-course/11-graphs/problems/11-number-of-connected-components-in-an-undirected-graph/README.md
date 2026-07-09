# Number of Connected Components in an Undirected Graph

**Difficulty:** Medium

## Problem

You have a graph of `n` nodes labeled from `0` to `n - 1`. You are given an integer `n` and an array `edges` where `edges[i] = [ai, bi]` indicates that there is an edge between `ai` and `bi` in the graph. Return the number of connected components in the graph.

## Examples

```
Input:  n = 5, edges = [[0,1],[1,2],[3,4]]
Output: 2
```

```
Input:  n = 5, edges = [[0,1],[1,2],[2,3],[3,4]]
Output: 1
```

## Constraints

- 1 <= n <= 2000
- 0 <= edges.length <= n * (n - 1) / 2

## Hints

1. Union-Find: each edge unites two components. The final count is the number of distinct roots.

## Solution

See [`../../solutions/11-number-of-connected-components-in-an-undirected-graph/`](../../solutions/11-number-of-connected-components-in-an-undirected-graph/) for the Python and Java 21 solutions and a step-by-step walkthrough.
