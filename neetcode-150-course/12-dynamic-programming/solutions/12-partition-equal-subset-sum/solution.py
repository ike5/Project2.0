"""Partition Equal Subset Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/12-partition-equal-subset-sum/solution.py
"""



def can_partition(nums: list[int]) -> bool:
    total = sum(nums)
    if total % 2: return False
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for x in nums:
        for s in range(target, x - 1, -1):
            if dp[s - x]:
                dp[s] = True
    return dp[target]


def _self_test() -> None:
    assert can_partition([1, 5, 11, 5]) == True, f"test 1 failed: got { can_partition([1, 5, 11, 5])!r } expected { True!r }"
    assert can_partition([1, 2, 3, 5]) == False, f"test 2 failed: got { can_partition([1, 2, 3, 5])!r } expected { False!r }"
    assert can_partition([2, 2]) == True, f"test 3 failed: got { can_partition([2, 2])!r } expected { True!r }"
    print(f"all 3 tests passed for can_partition")


if __name__ == "__main__":
    _self_test()
