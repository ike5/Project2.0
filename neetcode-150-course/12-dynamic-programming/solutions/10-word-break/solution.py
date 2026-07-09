"""Word Break.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/10-word-break/solution.py
"""



def word_break(s: str, word_dict: list[str]) -> bool:
    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]


def _self_test() -> None:
    assert word_break('leetcode', ['leet', 'code']) == True, f"test 1 failed: got { word_break('leetcode', ['leet', 'code'])!r } expected { True!r }"
    assert word_break('applepenapple', ['apple', 'pen']) == True, f"test 2 failed: got { word_break('applepenapple', ['apple', 'pen'])!r } expected { True!r }"
    assert word_break('catsandog', ['cats', 'dog', 'sand', 'and', 'cat']) == False, f"test 3 failed: got { word_break('catsandog', ['cats', 'dog', 'sand', 'and', 'cat'])!r } expected { False!r }"
    print(f"all 3 tests passed for word_break")


if __name__ == "__main__":
    _self_test()
