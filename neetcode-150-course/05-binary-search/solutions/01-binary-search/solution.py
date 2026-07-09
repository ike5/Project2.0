"""Binary Search.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-binary-search/solution.py
"""



def search(nums: list[int], target: int) -> int:
    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def _self_test() -> None:
    assert search([-1, 0, 3, 5, 9, 12], 9) == 4, f"test 1 failed: got { search([-1, 0, 3, 5, 9, 12], 9)!r } expected { 4!r }"
    assert search([-1, 0, 3, 5, 9, 12], 2) == -1, f"test 2 failed: got { search([-1, 0, 3, 5, 9, 12], 2)!r } expected { -1!r }"
    assert search([5], 5) == 0, f"test 3 failed: got { search([5], 5)!r } expected { 0!r }"
    assert search([1, 2, 3, 4, 5], 6) == -1, f"test 4 failed: got { search([1, 2, 3, 4, 5], 6)!r } expected { -1!r }"
    print(f"all 4 tests passed for search")


if __name__ == "__main__":
    _self_test()
