"""Longest Increasing Subsequence.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/11-longest-increasing-subsequence/solution.py
"""



def length_of_lis(nums: list[int]) -> int:
    import bisect
    tails: list[int] = []
    for x in nums:
        i = bisect.bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)


def _self_test() -> None:
    assert length_of_lis([10, 9, 2, 5, 3, 7, 101, 18]) == 4, f"test 1 failed: got { length_of_lis([10, 9, 2, 5, 3, 7, 101, 18])!r } expected { 4!r }"
    assert length_of_lis([0, 1, 0, 3, 2, 3]) == 4, f"test 2 failed: got { length_of_lis([0, 1, 0, 3, 2, 3])!r } expected { 4!r }"
    assert length_of_lis([7, 7, 7, 7, 7, 7, 7]) == 1, f"test 3 failed: got { length_of_lis([7, 7, 7, 7, 7, 7, 7])!r } expected { 1!r }"
    print(f"all 3 tests passed for length_of_lis")


if __name__ == "__main__":
    _self_test()
