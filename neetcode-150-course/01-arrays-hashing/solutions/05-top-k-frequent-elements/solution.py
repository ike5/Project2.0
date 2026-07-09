"""Top K Frequent Elements.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-top-k-frequent-elements/solution.py
"""



def top_k_frequent(nums: list[int], k: int) -> list[int]:
    from collections import Counter
    import heapq
    count = Counter(nums)
    return [x for x, _ in heapq.nlargest(k, count.items(), key=lambda p: p[1])]


def _self_test() -> None:
    assert top_k_frequent([1, 1, 1, 2, 2, 3], 2) == [1, 2], f"test 1 failed: got { top_k_frequent([1, 1, 1, 2, 2, 3], 2)!r } expected { [1, 2]!r }"
    assert top_k_frequent([1], 1) == [1], f"test 2 failed: got { top_k_frequent([1], 1)!r } expected { [1]!r }"
    assert top_k_frequent([1, 2, 3, 4, 5], 5) == [1, 2, 3, 4, 5], f"test 3 failed: got { top_k_frequent([1, 2, 3, 4, 5], 5)!r } expected { [1, 2, 3, 4, 5]!r }"
    assert top_k_frequent([4, 1, -1, 2, -1, 2, 3], 2) == [-1, 2], f"test 4 failed: got { top_k_frequent([4, 1, -1, 2, -1, 2, 3], 2)!r } expected { [-1, 2]!r }"
    print(f"all 4 tests passed for top_k_frequent")


if __name__ == "__main__":
    _self_test()
