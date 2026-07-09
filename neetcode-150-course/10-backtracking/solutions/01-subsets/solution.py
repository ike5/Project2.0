"""Subsets.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-subsets/solution.py
"""



def subsets(nums: list[int]) -> list[list[int]]:
    out: list[list[int]] = []

    def backtrack(i: int, path: list[int]) -> None:
        if i == len(nums):
            out.append(path.copy())
            return
        # skip nums[i]
        backtrack(i + 1, path)
        # include nums[i]
        path.append(nums[i])
        backtrack(i + 1, path)
        path.pop()

    backtrack(0, [])
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in subsets([1, 2, 3])]) == sorted([sorted(g) for g in [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]]), f"test 1 failed: got { sorted([sorted(g) for g in subsets([1, 2, 3])])!r } expected { sorted([sorted(g) for g in [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]])!r }"
    print(f"all 1 tests passed for subsets")


if __name__ == "__main__":
    _self_test()
