"""Interleaving String.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/18-interleaving-string/solution.py
"""



def is_interleave(s1: str, s2: str, s3: str) -> bool:
    if len(s1) + len(s2) != len(s3): return False
    m, n = len(s1), len(s2)
    dp = [False] * (n + 1)
    dp[0] = True
    for j in range(1, n + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, m + 1):
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, n + 1):
            dp[j] = (dp[j] and s1[i - 1] == s3[i + j - 1]) or \
                    (dp[j - 1] and s2[j - 1] == s3[i + j - 1])
    return dp[n]


def _self_test() -> None:
    assert is_interleave('aabcc', 'dbbca', 'aadbbcbcac') == True, f"test 1 failed: got { is_interleave('aabcc', 'dbbca', 'aadbbcbcac')!r } expected { True!r }"
    assert is_interleave('aabcc', 'dbbca', 'aadbbbaccc') == False, f"test 2 failed: got { is_interleave('aabcc', 'dbbca', 'aadbbbaccc')!r } expected { False!r }"
    assert is_interleave('', '', '') == True, f"test 3 failed: got { is_interleave('', '', '')!r } expected { True!r }"
    print(f"all 3 tests passed for is_interleave")


if __name__ == "__main__":
    _self_test()
