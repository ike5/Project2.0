"""Decode Ways.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-decode-ways/solution.py
"""



def num_decodings(s: str) -> int:
    if not s or s[0] == '0': return 0
    dp0, dp1 = 1, 1
    for i in range(1, len(s)):
        cur = 0
        if s[i] != '0':
            cur += dp1
        two = int(s[i - 1:i + 1])
        if 10 <= two <= 26:
            cur += dp0
        dp0, dp1 = dp1, cur
    return dp1


def _self_test() -> None:
    assert num_decodings('12') == 2, f"test 1 failed: got { num_decodings('12')!r } expected { 2!r }"
    assert num_decodings('226') == 3, f"test 2 failed: got { num_decodings('226')!r } expected { 3!r }"
    assert num_decodings('06') == 0, f"test 3 failed: got { num_decodings('06')!r } expected { 0!r }"
    assert num_decodings('10') == 1, f"test 4 failed: got { num_decodings('10')!r } expected { 1!r }"
    print(f"all 4 tests passed for num_decodings")


if __name__ == "__main__":
    _self_test()
