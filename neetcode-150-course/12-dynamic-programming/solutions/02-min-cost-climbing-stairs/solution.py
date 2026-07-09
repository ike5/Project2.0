"""Min Cost Climbing Stairs.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-min-cost-climbing-stairs/solution.py
"""



def min_cost_climbing_stairs(cost: list[int]) -> int:
    a, b = cost[0], cost[1]
    for i in range(2, len(cost)):
        a, b = b, cost[i] + min(a, b)
    return min(a, b)


def _self_test() -> None:
    assert min_cost_climbing_stairs([10, 15, 20]) == 15, f"test 1 failed: got { min_cost_climbing_stairs([10, 15, 20])!r } expected { 15!r }"
    assert min_cost_climbing_stairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1]) == 6, f"test 2 failed: got { min_cost_climbing_stairs([1, 100, 1, 1, 1, 100, 1, 1, 100, 1])!r } expected { 6!r }"
    print(f"all 2 tests passed for min_cost_climbing_stairs")


if __name__ == "__main__":
    _self_test()
