"""House Robber II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-house-robber-ii/solution.py
"""



def rob_circle(nums: list[int]) -> int:
    if len(nums) == 1: return nums[0]

    def helper(arr):
        a, b = arr[0], max(arr[0], arr[1])
        for i in range(2, len(arr)):
            a, b = b, max(b, a + arr[i])
        return b

    return max(helper(nums[:-1]), helper(nums[1:]))


def _self_test() -> None:
    assert rob_circle([2, 3, 2]) == 3, f"test 1 failed: got { rob_circle([2, 3, 2])!r } expected { 3!r }"
    assert rob_circle([1, 2, 3, 1]) == 4, f"test 2 failed: got { rob_circle([1, 2, 3, 1])!r } expected { 4!r }"
    assert rob_circle([0]) == 0, f"test 3 failed: got { rob_circle([0])!r } expected { 0!r }"
    print(f"all 3 tests passed for rob_circle")


if __name__ == "__main__":
    _self_test()
