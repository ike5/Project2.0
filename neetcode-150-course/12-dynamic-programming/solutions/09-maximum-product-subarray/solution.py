"""Maximum Product Subarray.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/09-maximum-product-subarray/solution.py
"""



def max_product(nums: list[int]) -> int:
    best = max_end = min_end = nums[0]
    for i in range(1, len(nums)):
        x = nums[i]
        if x < 0:
            max_end, min_end = min_end, max_end
        max_end = max(x, max_end * x)
        min_end = min(x, min_end * x)
        best = max(best, max_end)
    return best


def _self_test() -> None:
    assert max_product([2, 3, -2, 4]) == 6, f"test 1 failed: got { max_product([2, 3, -2, 4])!r } expected { 6!r }"
    assert max_product([-2, 0, -1]) == 0, f"test 2 failed: got { max_product([-2, 0, -1])!r } expected { 0!r }"
    assert max_product([-2]) == -2, f"test 3 failed: got { max_product([-2])!r } expected { -2!r }"
    print(f"all 3 tests passed for max_product")


if __name__ == "__main__":
    _self_test()
