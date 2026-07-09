"""Edit Distance.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/19-edit-distance/solution.py
"""



def min_distance(word1: str, word2: str) -> int:
    m, n = len(word1), len(word2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            tmp = dp[j]
            if word1[i - 1] == word2[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = tmp
    return dp[n]


def _self_test() -> None:
    assert min_distance('horse', 'ros') == 3, f"test 1 failed: got { min_distance('horse', 'ros')!r } expected { 3!r }"
    assert min_distance('intention', 'execution') == 5, f"test 2 failed: got { min_distance('intention', 'execution')!r } expected { 5!r }"
    print(f"all 2 tests passed for min_distance")


if __name__ == "__main__":
    _self_test()
