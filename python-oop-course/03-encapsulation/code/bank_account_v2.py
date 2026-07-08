"""A BankAccount that validates balance in the setter.

The trick: `self.balance = balance` in __init__ runs the setter, so the
negative-balance check fires on construction too.

Run:
    python 03-encapsulation/code/bank_account_v2.py
"""


class BankAccount:
    def __init__(self, owner: str, balance: float = 0) -> None:
        self.owner = owner
        self._balance = 0
        self.balance = balance                # triggers the setter

    @property
    def balance(self) -> float:
        return self._balance

    @balance.setter
    def balance(self, value: float) -> None:
        if value < 0:
            raise ValueError("balance must be >= 0")
        self._balance = value


def main() -> None:
    a = BankAccount("Ana", 100)
    print(a.owner, a.balance)
    a.balance = 250
    print(a.owner, a.balance)
    try:
        BankAccount("Bob", -1)
    except ValueError as e:
        print("blocked at construction:", e)


if __name__ == "__main__":
    main()
