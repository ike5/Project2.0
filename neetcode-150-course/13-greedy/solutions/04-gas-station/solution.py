"""Gas Station.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-gas-station/solution.py
"""



def can_complete_circuit(gas: list[int], cost: list[int]) -> int:
    if sum(gas) < sum(cost): return -1
    tank = 0
    start = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:
            start = i + 1
            tank = 0
    return start


def _self_test() -> None:
    assert can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]) == 3, f"test 1 failed: got { can_complete_circuit([1, 2, 3, 4, 5], [3, 4, 5, 1, 2])!r } expected { 3!r }"
    assert can_complete_circuit([2, 3, 4], [3, 4, 3]) == -1, f"test 2 failed: got { can_complete_circuit([2, 3, 4], [3, 4, 3])!r } expected { -1!r }"
    print(f"all 2 tests passed for can_complete_circuit")


if __name__ == "__main__":
    _self_test()
