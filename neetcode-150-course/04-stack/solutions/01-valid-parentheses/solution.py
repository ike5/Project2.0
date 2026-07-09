"""Valid Parentheses.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-valid-parentheses/solution.py
"""



def is_valid(s: str) -> bool:
    pairs = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    for c in s:
        if c in pairs:
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
        else:
            stack.append(c)
    return not stack


def _self_test() -> None:
    assert is_valid('()[]{}') == True, f"test 1 failed: got { is_valid('()[]{}')!r } expected { True!r }"
    assert is_valid('(]') == False, f"test 2 failed: got { is_valid('(]')!r } expected { False!r }"
    assert is_valid('([)]') == False, f"test 3 failed: got { is_valid('([)]')!r } expected { False!r }"
    assert is_valid('{[]}') == True, f"test 4 failed: got { is_valid('{[]}')!r } expected { True!r }"
    assert is_valid('') == True, f"test 5 failed: got { is_valid('')!r } expected { True!r }"
    print(f"all 5 tests passed for is_valid")


if __name__ == "__main__":
    _self_test()
