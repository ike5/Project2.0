"""Number of Connected Components in an Undirected Graph.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/11-number-of-connected-components-in-an-undirected-graph/solution.py
"""



def count_components(n: int, edges: list[list[int]]) -> int:
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(i) for i in range(n)})


def _self_test() -> None:
    assert count_components(5, [[0, 1], [1, 2], [3, 4]]) == 2, f"test 1 failed: got { count_components(5, [[0, 1], [1, 2], [3, 4]])!r } expected { 2!r }"
    assert count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]]) == 1, f"test 2 failed: got { count_components(5, [[0, 1], [1, 2], [2, 3], [3, 4]])!r } expected { 1!r }"
    print(f"all 2 tests passed for count_components")


if __name__ == "__main__":
    _self_test()
