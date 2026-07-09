"""Median of Two Sorted Arrays.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-median-of-two-sorted-arrays/solution.py
"""



def find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:
    # ensure nums1 is the smaller
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2
        j = (m + n + 1) // 2 - i
        left1 = nums1[i - 1] if i > 0 else float('-inf')
        right1 = nums1[i]     if i < m else float('inf')
        left2 = nums2[j - 1] if j > 0 else float('-inf')
        right2 = nums2[j]     if j < n else float('inf')
        if left1 <= right2 and left2 <= right1:
            if (m + n) % 2 == 1:
                return float(max(left1, left2))
            return (max(left1, left2) + min(right1, right2)) / 2.0
        if left1 > right2:
            hi = i - 1
        else:
            lo = i + 1
    return 0.0


def _self_test() -> None:
    assert find_median_sorted_arrays([1, 3], [2]) == 2.0, f"test 1 failed: got { find_median_sorted_arrays([1, 3], [2])!r } expected { 2.0!r }"
    assert find_median_sorted_arrays([1, 2], [3, 4]) == 2.5, f"test 2 failed: got { find_median_sorted_arrays([1, 2], [3, 4])!r } expected { 2.5!r }"
    assert find_median_sorted_arrays([], [1]) == 1.0, f"test 3 failed: got { find_median_sorted_arrays([], [1])!r } expected { 1.0!r }"
    print(f"all 3 tests passed for find_median_sorted_arrays")


if __name__ == "__main__":
    _self_test()
