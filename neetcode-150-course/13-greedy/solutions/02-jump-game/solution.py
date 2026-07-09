"""Jump Game.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-jump-game/solution.py
"""



def can_jump(nums: list[int]) -> bool:
    farthest = 0
    for i, x in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + x)
    return True


def _self_test() -> None:
    assert can_jump([2, 3, 1, 1, 4]) == True, f"test 1 failed: got { can_jump([2, 3, 1, 1, 4])!r } expected { True!r }"
    assert can_jump([3, 2, 1, 0, 4]) == False, f"test 2 failed: got { can_jump([3, 2, 1, 0, 4])!r } expected { False!r }"
    assert can_jump([0]) == True, f"test 3 failed: got { can_jump([0])!r } expected { True!r }"
    print(f"all 3 tests passed for can_jump")


if __name__ == "__main__":
    _self_test()
