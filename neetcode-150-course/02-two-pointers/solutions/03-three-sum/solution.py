"""3Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-three-sum/solution.py
"""



def three_sum(nums: list[int]) -> list[list[int]]:
    nums = sorted(nums)
    n = len(nums)
    out: list[list[int]] = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s == 0:
                out.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in three_sum([-1, 0, 1, 2, -1, -4])]) == sorted([sorted(g) for g in [[-1, -1, 2], [-1, 0, 1]]]), f"test 1 failed: got { sorted([sorted(g) for g in three_sum([-1, 0, 1, 2, -1, -4])])!r } expected { sorted([sorted(g) for g in [[-1, -1, 2], [-1, 0, 1]]])!r }"
    assert three_sum([0, 1, 1]) == [], f"test 2 failed: got { three_sum([0, 1, 1])!r } expected { []!r }"
    assert sorted([sorted(g) for g in three_sum([0, 0, 0])]) == sorted([sorted(g) for g in [[0, 0, 0]]]), f"test 3 failed: got { sorted([sorted(g) for g in three_sum([0, 0, 0])])!r } expected { sorted([sorted(g) for g in [[0, 0, 0]]])!r }"
    print(f"all 3 tests passed for three_sum")


if __name__ == "__main__":
    _self_test()
