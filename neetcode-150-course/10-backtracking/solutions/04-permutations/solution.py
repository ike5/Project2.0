"""Permutations.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-permutations/solution.py
"""



def permute(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []

    def backtrack(path: list[int], used: list[bool]) -> None:
        if len(path) == len(nums):
            out.append(path.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack(path, used)
            path.pop()
            used[i] = False

    backtrack([], [False] * len(nums))
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in permute([1, 2, 3])]) == sorted([sorted(g) for g in [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]]), f"test 1 failed: got { sorted([sorted(g) for g in permute([1, 2, 3])])!r } expected { sorted([sorted(g) for g in [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]])!r }"
    print(f"all 1 tests passed for permute")


if __name__ == "__main__":
    _self_test()
