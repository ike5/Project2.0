"""Sliding-window demo: max sum of any contiguous subarray of length k.

Run me: python 02-loops-and-iteration/code/max_sum_subarray.py
"""


def max_sum_brute(nums: list[int], k: int) -> int:
    n = len(nums)
    best = float("-inf")
    for i in range(n - k + 1):
        s = sum(nums[i:i + k])
        if s > best:
            best = s
    return best


def max_sum_sliding(nums: list[int], k: int) -> int:
    if not nums:
        return 0
    window = sum(nums[:k])
    best = window
    for i in range(k, len(nums)):
        window += nums[i] - nums[i - k]   # slide: add right, drop left
        if window > best:
            best = window
    return best


def main() -> None:
    nums = [2, 1, 5, 1, 3, 2]
    k = 3
    print("nums =", nums, "k =", k)
    print("brute   :", max_sum_brute(nums, k))
    print("sliding :", max_sum_sliding(nums, k))
    assert max_sum_brute(nums, k) == max_sum_sliding(nums, k)


if __name__ == "__main__":
    main()
