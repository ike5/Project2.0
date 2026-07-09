"""A tax strategy implemented as a class with __call__."""


class Bracket:
    def __init__(self, low: float, high: float, rate: float) -> None:
        self.low = low
        self.high = high
        self.rate = rate

    def __call__(self, amount: float) -> float:
        taxable = max(0.0, min(amount, self.high) - self.low)
        return taxable * self.rate


def main() -> None:
    # 0-1000 at 10%, 1000-5000 at 20%
    bracket1 = Bracket(0, 1000, 0.10)
    bracket2 = Bracket(1000, 5000, 0.20)

    # 1500 should be 100 (10% on 1000) + 100 (20% on 500) = 200
    combined = bracket1(1500) + bracket2(1500)
    print(f"combined tax on 1500 = {combined}")
    assert combined == 200.0
    print("OK: Bracket __call__ works.")


if __name__ == "__main__":
    main()
