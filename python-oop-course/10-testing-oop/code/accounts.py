"""A BankAccount to test against.

Run tests:
    pytest 10-testing-oop/code/test_accounts.py -v
"""


class BankAccount:
    def __init__(self, owner: str, balance: float = 0) -> None:
        if balance < 0:
            raise ValueError("balance must be >= 0")
        self.owner = owner
        self._balance = balance

    @property
    def balance(self) -> float:
        return self._balance

    def deposit(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self._balance += amount

    def withdraw(self, amount: float) -> None:
        if amount <= 0:
            raise ValueError("withdraw must be positive")
        if amount > self._balance:
            raise ValueError("insufficient funds")
        self._balance -= amount

    def __repr__(self) -> str:
        return f"BankAccount({self.owner!r}, balance={self._balance})"
