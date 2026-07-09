"""Longest Substring Without Repeating Characters.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-longest-substring-without-repeating-characters/solution.py
"""



def length_of_longest_substring(s: str) -> int:
    seen: set[str] = set()
    l = 0
    best = 0
    for r, c in enumerate(s):
        while c in seen:
            seen.remove(s[l])
            l += 1
        seen.add(c)
        best = max(best, r - l + 1)
    return best


def _self_test() -> None:
    assert length_of_longest_substring('abcabcbb') == 3, f"test 1 failed: got { length_of_longest_substring('abcabcbb')!r } expected { 3!r }"
    assert length_of_longest_substring('bbbbb') == 1, f"test 2 failed: got { length_of_longest_substring('bbbbb')!r } expected { 1!r }"
    assert length_of_longest_substring('pwwkew') == 3, f"test 3 failed: got { length_of_longest_substring('pwwkew')!r } expected { 3!r }"
    assert length_of_longest_substring('') == 0, f"test 4 failed: got { length_of_longest_substring('')!r } expected { 0!r }"
    assert length_of_longest_substring(' ') == 1, f"test 5 failed: got { length_of_longest_substring(' ')!r } expected { 1!r }"
    print(f"all 5 tests passed for length_of_longest_substring")


if __name__ == "__main__":
    _self_test()
