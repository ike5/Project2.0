"""Subsets II.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-subsets-ii/solution.py
"""



def subsets_with_dup(nums: list[int]) -> list[list[int]]:
    nums = sorted(nums)
    out: list[list[int]] = []

    def backtrack(i: int, path: list[int]) -> None:
        out.append(path.copy())
        for j in range(i, len(nums)):
            if j > i and nums[j] == nums[j - 1]:
                continue
            path.append(nums[j])
            backtrack(j + 1, path)
            path.pop()

    backtrack(0, [])
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in subsets_with_dup([1, 2, 2])]) == sorted([sorted(g) for g in [[], [1], [1, 2], [1, 2, 2], [2], [2, 2]]]), f"test 1 failed: got { sorted([sorted(g) for g in subsets_with_dup([1, 2, 2])])!r } expected { sorted([sorted(g) for g in [[], [1], [1, 2], [1, 2, 2], [2], [2, 2]]])!r }"
    print(f"all 1 tests passed for subsets_with_dup")


if __name__ == "__main__":
    _self_test()
