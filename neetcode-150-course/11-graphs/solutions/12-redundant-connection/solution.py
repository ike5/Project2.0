"""Redundant Connection.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/12-redundant-connection/solution.py
"""



def find_redundant_connection(edges: list[list[int]]) -> list[int]:
    n = len(edges)
    parent = list(range(n + 1))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return [a, b]
        parent[ra] = rb
    return []


def _self_test() -> None:
    assert find_redundant_connection([[1, 2], [1, 3], [2, 3]]) == [2, 3], f"test 1 failed: got { find_redundant_connection([[1, 2], [1, 3], [2, 3]])!r } expected { [2, 3]!r }"
    assert find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]]) == [1, 4], f"test 2 failed: got { find_redundant_connection([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]])!r } expected { [1, 4]!r }"
    print(f"all 2 tests passed for find_redundant_connection")


if __name__ == "__main__":
    _self_test()
