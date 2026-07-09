"""Longest Common Subsequence.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/14-longest-common-subsequence/solution.py
"""



def longest_common_subsequence(text1: str, text2: str) -> int:
    m, n = len(text1), len(text2)
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            tmp = dp[j]
            if text1[i - 1] == text2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = tmp
    return dp[n]


def _self_test() -> None:
    assert longest_common_subsequence('abcde', 'ace') == 3, f"test 1 failed: got { longest_common_subsequence('abcde', 'ace')!r } expected { 3!r }"
    assert longest_common_subsequence('abc', 'abc') == 3, f"test 2 failed: got { longest_common_subsequence('abc', 'abc')!r } expected { 3!r }"
    assert longest_common_subsequence('abc', 'def') == 0, f"test 3 failed: got { longest_common_subsequence('abc', 'def')!r } expected { 0!r }"
    print(f"all 3 tests passed for longest_common_subsequence")


if __name__ == "__main__":
    _self_test()
