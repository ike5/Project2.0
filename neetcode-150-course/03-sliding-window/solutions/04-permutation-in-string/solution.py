"""Permutation in String.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-permutation-in-string/solution.py
"""



def check_inclusion(s1: str, s2: str) -> bool:
    if len(s1) > len(s2):
        return False
    need = [0] * 26
    have = [0] * 26
    for c in s1:
        need[ord(c) - ord('a')] += 1
    for i in range(len(s1)):
        have[ord(s2[i]) - ord('a')] += 1
    if need == have:
        return True
    for i in range(len(s1), len(s2)):
        have[ord(s2[i]) - ord('a')] += 1
        have[ord(s2[i - len(s1)]) - ord('a')] -= 1
        if need == have:
            return True
    return False


def _self_test() -> None:
    assert check_inclusion('ab', 'eidbaooo') == True, f"test 1 failed: got { check_inclusion('ab', 'eidbaooo')!r } expected { True!r }"
    assert check_inclusion('ab', 'eidboaoo') == False, f"test 2 failed: got { check_inclusion('ab', 'eidboaoo')!r } expected { False!r }"
    assert check_inclusion('a', 'a') == True, f"test 3 failed: got { check_inclusion('a', 'a')!r } expected { True!r }"
    assert check_inclusion('abc', 'ccccbbbbaaaa') == False, f"test 4 failed: got { check_inclusion('abc', 'ccccbbbbaaaa')!r } expected { False!r }"
    print(f"all 4 tests passed for check_inclusion")


if __name__ == "__main__":
    _self_test()
