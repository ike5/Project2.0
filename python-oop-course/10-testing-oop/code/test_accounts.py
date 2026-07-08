"""Tests for the BankAccount class.

Run:
    pytest 10-testing-oop/code/test_accounts.py -v
"""

import pytest

from accounts import BankAccount


@pytest.fixture
def account():
    return BankAccount("Ana", 100)


def test_initial_balance(account):
    assert account.balance == 100
    assert account.owner == "Ana"


def test_deposit_increases_balance(account):
    account.deposit(50)
    assert account.balance == 150


def test_withdraw_decreases_balance(account):
    account.withdraw(30)
    assert account.balance == 70


def test_negative_initial_balance_raises():
    with pytest.raises(ValueError, match="balance must be >= 0"):
        BankAccount("X", -1)


@pytest.mark.parametrize("amount", [0, -1, -10])
def test_non_positive_deposit_raises(account, amount):
    with pytest.raises(ValueError, match="must be positive"):
        account.deposit(amount)


def test_overdraw_raises(account):
    with pytest.raises(ValueError, match="insufficient funds"):
        account.withdraw(10_000)
