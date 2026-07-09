"""Find Minimum in Rotated Sorted Array.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-find-minimum-in-rotated-sorted-array/solution.py
"""



def find_min(nums: list[int]) -> int:
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


def _self_test() -> None:
    assert find_min([3, 4, 5, 1, 2]) == 1, f"test 1 failed: got { find_min([3, 4, 5, 1, 2])!r } expected { 1!r }"
    assert find_min([4, 5, 6, 7, 0, 1, 2]) == 0, f"test 2 failed: got { find_min([4, 5, 6, 7, 0, 1, 2])!r } expected { 0!r }"
    assert find_min([11, 13, 15, 17]) == 11, f"test 3 failed: got { find_min([11, 13, 15, 17])!r } expected { 11!r }"
    print(f"all 3 tests passed for find_min")


if __name__ == "__main__":
    _self_test()
