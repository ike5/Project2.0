"""Daily Temperatures.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-daily-temperatures/solution.py
"""



def daily_temperatures(temperatures: list[int]) -> list[int]:
    n = len(temperatures)
    answer = [0] * n
    stack: list[int] = []   # indices, decreasing temperatures
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j
        stack.append(i)
    return answer


def _self_test() -> None:
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0], f"test 1 failed: got { daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73])!r } expected { [1, 1, 4, 2, 1, 1, 0, 0]!r }"
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0], f"test 2 failed: got { daily_temperatures([30, 40, 50, 60])!r } expected { [1, 1, 1, 0]!r }"
    assert daily_temperatures([90, 80, 70, 60]) == [0, 0, 0, 0], f"test 3 failed: got { daily_temperatures([90, 80, 70, 60])!r } expected { [0, 0, 0, 0]!r }"
    print(f"all 3 tests passed for daily_temperatures")


if __name__ == "__main__":
    _self_test()
