"""TaxCalculator with pluggable strategy functions.

Run me: python 04-strategy-pattern/code/tax.py
"""

from __future__ import annotations
from typing import Callable


class TaxCalculator:
    def __init__(self, strategy: Callable[[float], float]) -> None:
        self.strategy = strategy

    def compute(self, amount: float) -> float:
        return self.strategy(amount)


def flat_rate(amount: float) -> float:
    return amount * 0.15


def progressive(amount: float) -> float:
    return min(amount, 1000) * 0.10 + max(amount - 1000, 0) * 0.20


def zero(amount: float) -> float:
    return 0.0


def main() -> None:
    print(f"flat(1500)         = {TaxCalculator(flat_rate).compute(1500)}")
    print(f"progressive(1500)  = {TaxCalculator(progressive).compute(1500)}")
    print(f"zero(1500)         = {TaxCalculator(zero).compute(1500)}")
    print(f"lambda 10%(500)    = {TaxCalculator(lambda a: a * 0.10).compute(500)}")


if __name__ == "__main__":
    main()
