"""Product of Array Except Self.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-product-of-array-except-self/solution.py
"""



def product_except_self(nums: list[int]) -> list[int]:
    n = len(nums)
    answer = [1] * n
    # prefix products: answer[i] = product of nums[0..i-1]
    p = 1
    for i in range(n):
        answer[i] = p
        p *= nums[i]
    # suffix products: multiply by product of nums[i+1..n-1]
    s = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= s
        s *= nums[i]
    return answer


def _self_test() -> None:
    assert product_except_self([1, 2, 3, 4]) == [24, 12, 8, 6], f"test 1 failed: got { product_except_self([1, 2, 3, 4])!r } expected { [24, 12, 8, 6]!r }"
    assert product_except_self([-1, 1, 0, -3, 3]) == [0, 0, 9, 0, 0], f"test 2 failed: got { product_except_self([-1, 1, 0, -3, 3])!r } expected { [0, 0, 9, 0, 0]!r }"
    assert product_except_self([2, 3]) == [3, 2], f"test 3 failed: got { product_except_self([2, 3])!r } expected { [3, 2]!r }"
    print(f"all 3 tests passed for product_except_self")


if __name__ == "__main__":
    _self_test()
