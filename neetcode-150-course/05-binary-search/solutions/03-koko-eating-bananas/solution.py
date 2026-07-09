"""Koko Eating Bananas.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-koko-eating-bananas/solution.py
"""



def min_eating_speed(piles: list[int], h: int) -> int:
    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        hours = sum((p + mid - 1) // mid for p in piles)   # ceil(p / mid)
        if hours <= h:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _self_test() -> None:
    assert min_eating_speed([1, 4, 3, 2], 9) == 2, f"test 1 failed: got { min_eating_speed([1, 4, 3, 2], 9)!r } expected { 2!r }"
    assert min_eating_speed([25, 10, 23, 4], 4) == 25, f"test 2 failed: got { min_eating_speed([25, 10, 23, 4], 4)!r } expected { 25!r }"
    assert min_eating_speed([3, 6, 7, 11], 8) == 4, f"test 3 failed: got { min_eating_speed([3, 6, 7, 11], 8)!r } expected { 4!r }"
    print(f"all 3 tests passed for min_eating_speed")


if __name__ == "__main__":
    _self_test()
