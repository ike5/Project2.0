"""Search in Rotated Sorted Array.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-search-in-rotated-sorted-array/solution.py
"""



def search_rotated(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:                  # left half sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:                                      # right half sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1


def _self_test() -> None:
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 0) == 4, f"test 1 failed: got { search_rotated([4, 5, 6, 7, 0, 1, 2], 0)!r } expected { 4!r }"
    assert search_rotated([4, 5, 6, 7, 0, 1, 2], 3) == -1, f"test 2 failed: got { search_rotated([4, 5, 6, 7, 0, 1, 2], 3)!r } expected { -1!r }"
    assert search_rotated([1], 0) == -1, f"test 3 failed: got { search_rotated([1], 0)!r } expected { -1!r }"
    assert search_rotated([3, 1], 1) == 1, f"test 4 failed: got { search_rotated([3, 1], 1)!r } expected { 1!r }"
    print(f"all 4 tests passed for search_rotated")


if __name__ == "__main__":
    _self_test()
