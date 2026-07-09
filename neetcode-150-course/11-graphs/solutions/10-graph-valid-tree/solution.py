"""Graph Valid Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/10-graph-valid-tree/solution.py
"""



def valid_tree(n: int, edges: list[list[int]]) -> bool:
    if len(edges) != n - 1:
        return False
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
    return True


def _self_test() -> None:
    assert valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]]) == True, f"test 1 failed: got { valid_tree(5, [[0, 1], [0, 2], [0, 3], [1, 4]])!r } expected { True!r }"
    assert valid_tree(5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]) == False, f"test 2 failed: got { valid_tree(5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]])!r } expected { False!r }"
    print(f"all 2 tests passed for valid_tree")


if __name__ == "__main__":
    _self_test()
