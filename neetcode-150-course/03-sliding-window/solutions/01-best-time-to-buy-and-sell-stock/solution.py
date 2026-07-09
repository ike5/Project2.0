"""Best Time to Buy and Sell Stock.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-best-time-to-buy-and-sell-stock/solution.py
"""



def max_profit(prices: list[int]) -> int:
    min_price = float('inf')
    best = 0
    for p in prices:
        if p < min_price:
            min_price = p
        else:
            best = max(best, p - min_price)
    return best


def _self_test() -> None:
    assert max_profit([7, 1, 5, 3, 6, 4]) == 5, f"test 1 failed: got { max_profit([7, 1, 5, 3, 6, 4])!r } expected { 5!r }"
    assert max_profit([7, 6, 4, 3, 1]) == 0, f"test 2 failed: got { max_profit([7, 6, 4, 3, 1])!r } expected { 0!r }"
    assert max_profit([2, 4, 1]) == 2, f"test 3 failed: got { max_profit([2, 4, 1])!r } expected { 2!r }"
    assert max_profit([1]) == 0, f"test 4 failed: got { max_profit([1])!r } expected { 0!r }"
    print(f"all 4 tests passed for max_profit")


if __name__ == "__main__":
    _self_test()
