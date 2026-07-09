"""Target Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/17-target-sum/solution.py
"""



def find_target_sum_ways(nums: list[int], target: int) -> int:
    total = sum(nums)
    if abs(target) > total: return 0
    if (total + target) % 2: return 0
    p = (total + target) // 2
    dp = [0] * (p + 1)
    dp[0] = 1
    for x in nums:
        for s in range(p, x - 1, -1):
            dp[s] += dp[s - x]
    return dp[p]


def _self_test() -> None:
    assert find_target_sum_ways([1, 1, 1, 1, 1], 3) == 5, f"test 1 failed: got { find_target_sum_ways([1, 1, 1, 1, 1], 3)!r } expected { 5!r }"
    assert find_target_sum_ways([1], 1) == 1, f"test 2 failed: got { find_target_sum_ways([1], 1)!r } expected { 1!r }"
    print(f"all 2 tests passed for find_target_sum_ways")


if __name__ == "__main__":
    _self_test()
