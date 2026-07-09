"""Last Stone Weight.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-last-stone-weight/solution.py
"""



def last_stone_weight(stones: list[int]) -> int:
    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        a = -heapq.heappop(heap)
        b = -heapq.heappop(heap)
        if a != b:
            heapq.heappush(heap, -(a - b))
    return -heap[0] if heap else 0


def _self_test() -> None:
    assert last_stone_weight([2, 7, 4, 1, 8, 1]) == 1, f"test 1 failed: got { last_stone_weight([2, 7, 4, 1, 8, 1])!r } expected { 1!r }"
    assert last_stone_weight([1]) == 1, f"test 2 failed: got { last_stone_weight([1])!r } expected { 1!r }"
    assert last_stone_weight([2, 2]) == 0, f"test 3 failed: got { last_stone_weight([2, 2])!r } expected { 0!r }"
    print(f"all 3 tests passed for last_stone_weight")


if __name__ == "__main__":
    _self_test()
