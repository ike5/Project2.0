"""Letter Combinations of a Phone Number.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-letter-combinations-of-a-phone-number/solution.py
"""



def letter_combinations(digits: str) -> list[str]:
    if not digits:
        return []
    mapping = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz',
    }
    out: list[str] = []

    def backtrack(i: int, path: list[str]) -> None:
        if i == len(digits):
            out.append(''.join(path))
            return
        for c in mapping[digits[i]]:
            path.append(c)
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return out


def _self_test() -> None:
    assert letter_combinations('23') == ['ad', 'ae', 'af', 'bd', 'be', 'bf', 'cd', 'ce', 'cf'], f"test 1 failed: got { letter_combinations('23')!r } expected { ['ad', 'ae', 'af', 'bd', 'be', 'bf', 'cd', 'ce', 'cf']!r }"
    assert letter_combinations('') == [], f"test 2 failed: got { letter_combinations('')!r } expected { []!r }"
    assert letter_combinations('2') == ['a', 'b', 'c'], f"test 3 failed: got { letter_combinations('2')!r } expected { ['a', 'b', 'c']!r }"
    print(f"all 3 tests passed for letter_combinations")


if __name__ == "__main__":
    _self_test()
