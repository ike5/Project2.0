"""Evaluate Reverse Polish Notation.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-evaluate-reverse-polish-notation/solution.py
"""



def eval_rpn(tokens: list[str]) -> int:
    stack: list[int] = []
    ops = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: int(a / b),  # truncate toward zero
    }
    for t in tokens:
        if t in ops:
            b = stack.pop()
            a = stack.pop()
            stack.append(ops[t](a, b))
        else:
            stack.append(int(t))
    return stack[-1]


def _self_test() -> None:
    assert eval_rpn(['2', '1', '+', '3', '*']) == 9, f"test 1 failed: got { eval_rpn(['2', '1', '+', '3', '*'])!r } expected { 9!r }"
    assert eval_rpn(['4', '13', '5', '/', '+']) == 6, f"test 2 failed: got { eval_rpn(['4', '13', '5', '/', '+'])!r } expected { 6!r }"
    assert eval_rpn(['10', '6', '9', '3', '+', '-11', '*', '/', '*', '17', '+', '5', '+']) == 22, f"test 3 failed: got { eval_rpn(['10', '6', '9', '3', '+', '-11', '*', '/', '*', '17', '+', '5', '+'])!r } expected { 22!r }"
    print(f"all 3 tests passed for eval_rpn")


if __name__ == "__main__":
    _self_test()
