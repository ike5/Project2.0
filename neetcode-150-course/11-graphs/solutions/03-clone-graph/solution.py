"""Clone Graph.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-clone-graph/solution.py
"""

class GraphNode:
    """A minimal undirected graph node."""
    def __init__(self, val: int = 0,
                 neighbors: "list[GraphNode] | None" = None) -> None:
        self.val = val
        self.neighbors = neighbors if neighbors is not None else []


def build_graph(adj: list[list[int]]) -> "GraphNode | None":
    """Build an undirected graph from an adjacency list of int neighbor ids.
    Returns the node with id 1, or None for an empty graph.
    Assumes nodes are labeled 1..N."""
    if not adj:
        return None
    n = len(adj)
    nodes = [GraphNode(i + 1) for i in range(n)]
    for i, nbrs in enumerate(adj):
        for j in nbrs:
            nodes[i].neighbors.append(nodes[j - 1])
    return nodes[0]



def clone_graph(adj: list[list[int]]) -> int:
    # Build the graph from adjacency list, clone it, return the count of distinct nodes
    g = build_graph(adj)
    if g is None: return 0
    cloned: dict[int, GraphNode] = {}

    def dfs(n):
        if n.val in cloned:
            return cloned[n.val]
        copy = GraphNode(n.val)
        cloned[n.val] = copy
        copy.neighbors = [dfs(nb) for nb in n.neighbors]
        return copy

    dfs(g)
    return len(cloned)


def _self_test() -> None:
    assert clone_graph([[2], [1]]) == 2, f"test 1 failed: got { clone_graph([[2], [1]])!r } expected { 2!r }"
    assert clone_graph([[2, 3], [1, 3], [1, 2]]) == 3, f"test 2 failed: got { clone_graph([[2, 3], [1, 3], [1, 2]])!r } expected { 3!r }"
    assert clone_graph([]) == 0, f"test 3 failed: got { clone_graph([])!r } expected { 0!r }"
    print(f"all 3 tests passed for clone_graph")


if __name__ == "__main__":
    _self_test()
