"""Longest Palindromic Substring.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-longest-palindromic-substring/solution.py
"""



def longest_palindrome(s: str) -> str:
    def expand(l: int, r: int) -> int:
        while l >= 0 and r < len(s) and s[l] == s[r]:
            l -= 1
            r += 1
        return r - l - 1   # length of the palindrome

    best_l, best_len = 0, 0
    for i in range(len(s)):
        l1 = expand(i, i)
        l2 = expand(i, i + 1)
        m = max(l1, l2)
        if m > best_len:
            best_len = m
            best_l = i - (m - 1) // 2
    return s[best_l:best_l + best_len]


def _self_test() -> None:
    assert longest_palindrome('babad') == 'bab', f"test 1 failed: got { longest_palindrome('babad')!r } expected { 'bab'!r }"
    assert longest_palindrome('cbbd') == 'bb', f"test 2 failed: got { longest_palindrome('cbbd')!r } expected { 'bb'!r }"
    print(f"all 2 tests passed for longest_palindrome")


if __name__ == "__main__":
    _self_test()
