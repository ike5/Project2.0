"""Maximum Subarray.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-maximum-subarray/solution.py
"""



def max_subarray(nums: list[int]) -> int:
    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def _self_test() -> None:
    assert max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]) == 6, f"test 1 failed: got { max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4])!r } expected { 6!r }"
    assert max_subarray([1]) == 1, f"test 2 failed: got { max_subarray([1])!r } expected { 1!r }"
    assert max_subarray([5, 4, -1, 7, 8]) == 23, f"test 3 failed: got { max_subarray([5, 4, -1, 7, 8])!r } expected { 23!r }"
    print(f"all 3 tests passed for max_subarray")


if __name__ == "__main__":
    _self_test()
