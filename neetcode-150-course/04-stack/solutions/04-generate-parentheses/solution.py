"""Generate Parentheses.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-generate-parentheses/solution.py
"""



def generate_parenthesis(n: int) -> list[str]:
    out: list[str] = []

    def backtrack(s: str, opens: int, closes: int) -> None:
        if len(s) == 2 * n:
            out.append(s)
            return
        if opens < n:
            backtrack(s + '(', opens + 1, closes)
        if closes < opens:
            backtrack(s + ')', opens, closes + 1)

    backtrack('', 0, 0)
    return out


def _self_test() -> None:
    assert generate_parenthesis(3) == ['((()))', '(()())', '(())()', '()(())', '()()()'], f"test 1 failed: got { generate_parenthesis(3)!r } expected { ['((()))', '(()())', '(())()', '()(())', '()()()']!r }"
    assert generate_parenthesis(1) == ['()'], f"test 2 failed: got { generate_parenthesis(1)!r } expected { ['()']!r }"
    print(f"all 2 tests passed for generate_parenthesis")


if __name__ == "__main__":
    _self_test()
