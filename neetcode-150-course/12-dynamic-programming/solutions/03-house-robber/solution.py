"""House Robber.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-house-robber/solution.py
"""



def rob(nums: list[int]) -> int:
    if not nums: return 0
    if len(nums) == 1: return nums[0]
    a, b = nums[0], max(nums[0], nums[1])
    for i in range(2, len(nums)):
        a, b = b, max(b, a + nums[i])
    return b


def _self_test() -> None:
    assert rob([1, 2, 3, 1]) == 4, f"test 1 failed: got { rob([1, 2, 3, 1])!r } expected { 4!r }"
    assert rob([2, 7, 9, 3, 1]) == 12, f"test 2 failed: got { rob([2, 7, 9, 3, 1])!r } expected { 12!r }"
    print(f"all 2 tests passed for rob")


if __name__ == "__main__":
    _self_test()
