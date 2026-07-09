"""Maximal Square.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/22-maximal-square/solution.py
"""



def maximal_square(matrix: list[list[str]]) -> int:
    m, n = len(matrix), len(matrix[0])
    dp = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            tmp = dp[j]
            if matrix[i - 1][j - 1] == '1':
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                best = max(best, dp[j])
            else:
                dp[j] = 0
            prev = tmp
    return best * best


def _self_test() -> None:
    assert maximal_square([['1', '0', '1', '0', '0'], ['1', '0', '1', '1', '1'], ['1', '1', '1', '1', '1'], ['1', '0', '0', '1', '0']]) == 4, f"test 1 failed: got { maximal_square([['1', '0', '1', '0', '0'], ['1', '0', '1', '1', '1'], ['1', '1', '1', '1', '1'], ['1', '0', '0', '1', '0']])!r } expected { 4!r }"
    assert maximal_square([['0', '1'], ['1', '0']]) == 1, f"test 2 failed: got { maximal_square([['0', '1'], ['1', '0']])!r } expected { 1!r }"
    print(f"all 2 tests passed for maximal_square")


if __name__ == "__main__":
    _self_test()
