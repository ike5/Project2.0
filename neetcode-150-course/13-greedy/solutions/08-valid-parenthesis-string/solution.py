"""Valid Parenthesis String.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-valid-parenthesis-string/solution.py
"""



def check_valid_string(s: str) -> bool:
    lo = hi = 0
    for c in s:
        if c == '(':
            lo += 1; hi += 1
        elif c == ')':
            lo = max(lo - 1, 0)
            hi -= 1
        else:  # *
            lo = max(lo - 1, 0)  # if * is ')'
            hi += 1               # if * is '('
        if hi < 0:
            return False
    return lo == 0


def _self_test() -> None:
    assert check_valid_string('()') == True, f"test 1 failed: got { check_valid_string('()')!r } expected { True!r }"
    assert check_valid_string('(*)') == True, f"test 2 failed: got { check_valid_string('(*)')!r } expected { True!r }"
    assert check_valid_string('(*))') == True, f"test 3 failed: got { check_valid_string('(*))')!r } expected { True!r }"
    assert check_valid_string('(((*)') == False, f"test 4 failed: got { check_valid_string('(((*)')!r } expected { False!r }"
    print(f"all 4 tests passed for check_valid_string")


if __name__ == "__main__":
    _self_test()
