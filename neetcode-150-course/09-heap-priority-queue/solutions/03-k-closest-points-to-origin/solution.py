"""K Closest Points to Origin.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-k-closest-points-to-origin/solution.py
"""



def k_closest(points: list[list[int]], k: int) -> list[list[int]]:
    import heapq
    heap: list[tuple[int, list[int]]] = []
    for p in points:
        d = p[0] * p[0] + p[1] * p[1]
        heapq.heappush(heap, (-d, p))
        if len(heap) > k:
            heapq.heappop(heap)
    return [p for _, p in heap]


def _self_test() -> None:
    assert sorted([sorted(g) for g in k_closest([[1, 3], [-2, 2]], 2)]) == sorted([sorted(g) for g in [[-2, 2], [1, 3]]]), f"test 1 failed: got { sorted([sorted(g) for g in k_closest([[1, 3], [-2, 2]], 2)])!r } expected { sorted([sorted(g) for g in [[-2, 2], [1, 3]]])!r }"
    assert sorted([sorted(g) for g in k_closest([[3, 3], [5, -1], [-2, 4]], 2)]) == sorted([sorted(g) for g in [[3, 3], [-2, 4]]]), f"test 2 failed: got { sorted([sorted(g) for g in k_closest([[3, 3], [5, -1], [-2, 4]], 2)])!r } expected { sorted([sorted(g) for g in [[3, 3], [-2, 4]]])!r }"
    print(f"all 2 tests passed for k_closest")


if __name__ == "__main__":
    _self_test()
