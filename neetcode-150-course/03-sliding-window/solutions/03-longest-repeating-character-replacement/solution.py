"""Longest Repeating Character Replacement.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-longest-repeating-character-replacement/solution.py
"""



def character_replacement(s: str, k: int) -> int:
    from collections import Counter
    counts: Counter[str] = Counter()
    l = 0
    best = 0
    max_count = 0
    for r, c in enumerate(s):
        counts[c] += 1
        max_count = max(max_count, counts[c])
        if (r - l + 1) - max_count > k:
            counts[s[l]] -= 1
            l += 1
        best = max(best, r - l + 1)
    return best


def _self_test() -> None:
    assert character_replacement('ABAB', 2) == 4, f"test 1 failed: got { character_replacement('ABAB', 2)!r } expected { 4!r }"
    assert character_replacement('AABABBA', 1) == 4, f"test 2 failed: got { character_replacement('AABABBA', 1)!r } expected { 4!r }"
    assert character_replacement('AAAA', 0) == 4, f"test 3 failed: got { character_replacement('AAAA', 0)!r } expected { 4!r }"
    print(f"all 3 tests passed for character_replacement")


if __name__ == "__main__":
    _self_test()
