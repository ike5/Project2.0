"""Valid Anagram.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-valid-anagram/solution.py
"""



def is_anagram(s: str, t: str) -> bool:
    from collections import Counter
    return Counter(s) == Counter(t)


def _self_test() -> None:
    assert is_anagram('anagram', 'nagaram') == True, f"test 1 failed: got { is_anagram('anagram', 'nagaram')!r } expected { True!r }"
    assert is_anagram('rat', 'car') == False, f"test 2 failed: got { is_anagram('rat', 'car')!r } expected { False!r }"
    assert is_anagram('a', 'a') == True, f"test 3 failed: got { is_anagram('a', 'a')!r } expected { True!r }"
    assert is_anagram('ab', 'a') == False, f"test 4 failed: got { is_anagram('ab', 'a')!r } expected { False!r }"
    assert is_anagram('', '') == True, f"test 5 failed: got { is_anagram('', '')!r } expected { True!r }"
    print(f"all 5 tests passed for is_anagram")


if __name__ == "__main__":
    _self_test()
