"""Minimum Size Subarray Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-minimum-size-subarray-sum/solution.py
"""



def min_sub_array_len(target: int, nums: list[int]) -> int:
    l = 0
    s = 0
    best = float('inf')
    for r in range(len(nums)):
        s += nums[r]
        while s >= target:
            best = min(best, r - l + 1)
            s -= nums[l]
            l += 1
    return 0 if best == float('inf') else best


def _self_test() -> None:
    assert min_sub_array_len(7, [2, 3, 1, 2, 4, 3]) == 2, f"test 1 failed: got { min_sub_array_len(7, [2, 3, 1, 2, 4, 3])!r } expected { 2!r }"
    assert min_sub_array_len(4, [1, 4, 4]) == 1, f"test 2 failed: got { min_sub_array_len(4, [1, 4, 4])!r } expected { 1!r }"
    assert min_sub_array_len(11, [1, 1, 1, 1, 1, 1, 1, 1]) == 0, f"test 3 failed: got { min_sub_array_len(11, [1, 1, 1, 1, 1, 1, 1, 1])!r } expected { 0!r }"
    print(f"all 3 tests passed for min_sub_array_len")


if __name__ == "__main__":
    _self_test()
