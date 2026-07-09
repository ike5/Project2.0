"""Palindromic Substrings.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-palindromic-substrings/solution.py
"""



def count_substrings(s: str) -> int:
    count = 0

    def expand(l: int, r: int) -> None:
        nonlocal count
        while l >= 0 and r < len(s) and s[l] == s[r]:
            count += 1
            l -= 1
            r += 1

    for i in range(len(s)):
        expand(i, i)
        expand(i, i + 1)
    return count


def _self_test() -> None:
    assert count_substrings('abc') == 3, f"test 1 failed: got { count_substrings('abc')!r } expected { 3!r }"
    assert count_substrings('aaa') == 6, f"test 2 failed: got { count_substrings('aaa')!r } expected { 6!r }"
    print(f"all 2 tests passed for count_substrings")


if __name__ == "__main__":
    _self_test()
