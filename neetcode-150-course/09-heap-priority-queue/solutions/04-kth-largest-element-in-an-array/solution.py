"""Kth Largest Element in an Array.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-kth-largest-element-in-an-array/solution.py
"""



def kth_largest(nums: list[int], k: int) -> int:
    import heapq
    return heapq.nlargest(k, nums)[-1]


def _self_test() -> None:
    assert kth_largest([3, 2, 1, 5, 6, 4], 2) == 5, f"test 1 failed: got { kth_largest([3, 2, 1, 5, 6, 4], 2)!r } expected { 5!r }"
    assert kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4, f"test 2 failed: got { kth_largest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4)!r } expected { 4!r }"
    print(f"all 2 tests passed for kth_largest")


if __name__ == "__main__":
    _self_test()
