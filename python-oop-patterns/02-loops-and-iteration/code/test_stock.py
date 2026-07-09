"""pytest tests for max profit."""

import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from stock import max_profit_brute, max_profit_kadane, max_profit_min_sofar


def test_basic():
    prices = [7, 1, 5, 3, 6, 4]
    assert max_profit_min_sofar(prices) == 5
    assert max_profit_kadane(prices) == 5
    assert max_profit_brute(prices) == 5


def test_decreasing():
    prices = [7, 6, 4, 3, 1]
    assert max_profit_min_sofar(prices) == 0
    assert max_profit_kadane(prices) == 0


def test_all_solutions_agree_on_random():
    import random
    random.seed(0)
    prices = [random.randint(0, 100) for _ in range(20)]
    assert max_profit_brute(prices) == max_profit_min_sofar(prices) == max_profit_kadane(prices)
