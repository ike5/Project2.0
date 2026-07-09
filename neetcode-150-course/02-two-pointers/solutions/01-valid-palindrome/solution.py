"""Valid Palindrome.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-valid-palindrome/solution.py
"""



def is_palindrome(s: str) -> bool:
    l, r = 0, len(s) - 1
    while l < r:
        while l < r and not s[l].isalnum():
            l += 1
        while l < r and not s[r].isalnum():
            r -= 1
        if s[l].lower() != s[r].lower():
            return False
        l += 1
        r -= 1
    return True


def _self_test() -> None:
    assert is_palindrome('A man, a plan, a canal: Panama') == True, f"test 1 failed: got { is_palindrome('A man, a plan, a canal: Panama')!r } expected { True!r }"
    assert is_palindrome('race a car') == False, f"test 2 failed: got { is_palindrome('race a car')!r } expected { False!r }"
    assert is_palindrome(' ') == True, f"test 3 failed: got { is_palindrome(' ')!r } expected { True!r }"
    assert is_palindrome('a') == True, f"test 4 failed: got { is_palindrome('a')!r } expected { True!r }"
    assert is_palindrome('ab') == False, f"test 5 failed: got { is_palindrome('ab')!r } expected { False!r }"
    print(f"all 5 tests passed for is_palindrome")


if __name__ == "__main__":
    _self_test()
