# Clone Graph - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

Given a reference of a node in a **connected** undirected graph, return a deep copy (clone) of the graph. Each node in the graph contains a value (`int`) and a list (`List[Node]`) of its neighbors.

## Examples

- `adjList = [[2,4],[1,3],[2,4],[1,3]]` &rarr; `Same structure, new nodes`

## Constraints

- 0 <= number of nodes <= 100
- 1 <= Node.val <= 100

## Intuition

DFS with a `dict[old_id, new_node]`. When we revisit a node, we
return the already-created copy — this prevents infinite recursion in
the presence of cycles.

**Time:** O(V + E). **Space:** O(V) for the map and recursion.

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
