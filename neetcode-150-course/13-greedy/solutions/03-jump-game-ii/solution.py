"""Jump Game II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-jump-game-ii/solution.py
"""



def jump(nums: list[int]) -> int:
    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps


def _self_test() -> None:
    assert jump([2, 3, 1, 1, 4]) == 2, f"test 1 failed: got { jump([2, 3, 1, 1, 4])!r } expected { 2!r }"
    assert jump([2, 3, 0, 1, 4]) == 2, f"test 2 failed: got { jump([2, 3, 0, 1, 4])!r } expected { 2!r }"
    print(f"all 2 tests passed for jump")


if __name__ == "__main__":
    _self_test()
