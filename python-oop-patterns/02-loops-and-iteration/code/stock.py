"""Three solutions to Best Time to Buy and Sell Stock.

Run me: python 02-loops-and-iteration/code/stock.py
"""

import time
import random


def max_profit_brute(prices: list[int]) -> int:
    n = len(prices)
    best = 0
    for i in range(n):
        for j in range(i + 1, n):
            if prices[j] - prices[i] > best:
                best = prices[j] - prices[i]
    return best


def max_profit_min_sofar(prices: list[int]) -> int:
    """O(n) — track the minimum price seen so far."""
    min_sofar = prices[0]
    best = 0
    for price in prices[1:]:
        if price < min_sofar:
            min_sofar = price
        elif price - min_sofar > best:
            best = price - min_sofar
    return best


def max_profit_kadane(prices: list[int]) -> int:
    """Kadane's on day-to-day differences."""
    best = 0
    cur = 0
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        cur = max(0, cur + diff)
        best = max(best, cur)
    return best


def benchmark(label, fn, prices, runs=5):
    best = float("inf")
    result = None
    for _ in range(runs):
        t0 = time.perf_counter()
        result = fn(prices)
        best = min(best, time.perf_counter() - t0)
    print(f"  {label:6s}: {result}   in {best:.6f} s")
    return result


def main() -> None:
    random.seed(0)

    for n in (200, 2_000, 5_000):
        prices = [random.randint(0, 1000) for _ in range(n)]
        print(f"\n--- n = {n} ---")
        if n <= 2_000:
            r1 = benchmark("brute", max_profit_brute, prices)
        else:
            r1 = None
            print("  brute: skipped (would take too long)")
        r2 = benchmark("min", max_profit_min_sofar, prices)
        r3 = benchmark("kadan", max_profit_kadane, prices)
        if r1 is not None:
            assert r1 == r2 == r3
        else:
            assert r2 == r3


if __name__ == "__main__":
    main()
