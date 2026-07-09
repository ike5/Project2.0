# Clone Graph

**Difficulty:** Medium

## Problem

Given a reference of a node in a **connected** undirected graph, return a deep copy (clone) of the graph. Each node in the graph contains a value (`int`) and a list (`List[Node]`) of its neighbors.

## Examples

```
Input:  adjList = [[2,4],[1,3],[2,4],[1,3]]
Output: Same structure, new nodes
```

## Constraints

- 0 <= number of nodes <= 100
- 1 <= Node.val <= 100

## Hints

1. DFS, building a `dict[old, new]` as you go. Return `new_node` for each `old_node`.

## Solution

See [`../../solutions/03-clone-graph/`](../../solutions/03-clone-graph/) for the Python and Java 21 solutions and a step-by-step walkthrough.
