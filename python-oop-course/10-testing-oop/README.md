# Module 10 — Testing OOP

**Goal:** Test your classes with `pytest` — write good unit tests, use fixtures, mock collaborators, and measure coverage. ⏱️ ~2 h · 🎯 Prereq: 09.

---

## 1. Why test classes differently from scripts?

A well-designed class is *easier* to test than a tangled function:

- You can construct a small, focused instance in setup and exercise one method.
- Dependencies are *injected* (or can be) via `__init__`, so you can pass fakes.
- Methods return values or raise exceptions — both are great for assertions.

The flip side: a class with hidden state and implicit dependencies is *hard* to test. The discipline of writing tests pushes you toward better design.

## 2. The minimum: a function named `test_*`

`pytest` discovers files named `test_*.py` (or `*_test.py`) and within them, functions and methods named `test_*`. A test passes if it returns without raising. Assertions are how you check things.

```python
from bank import BankAccount

def test_deposit_increases_balance():
    a = BankAccount("Ana", 100)
    a.deposit(50)
    assert a.balance == 150
```

That's the whole minimum. Run it with `pytest path/to/test_file.py -v`.

## 3. Asserting exceptions

Use `pytest.raises` to assert a block raises a specific exception:

```python
import pytest

def test_negative_deposit_raises():
    a = BankAccount("Ana", 0)
    with pytest.raises(ValueError):
        a.deposit(-1)
```

You can also inspect the exception's message:

```python
with pytest.raises(ValueError, match="must be positive"):
    a.deposit(-1)
```

## 4. Fixtures: shared setup

A **fixture** is a function decorated with `@pytest.fixture` that produces a value (or does setup) for tests to use. Tests request fixtures by naming them as parameters.

```python
import pytest

@pytest.fixture
def account():
    return BankAccount("Ana", 100)

def test_deposit(account):
    account.deposit(50)
    assert account.balance == 150

def test_withdraw(account):
    account.withdraw(30)
    assert account.balance == 70
```

Each test gets a *fresh* fixture. Fixtures can depend on other fixtures (`def bigger_setup(account): ...`). You can scope fixtures to a module or session when setup is expensive.

> **Tip:** name fixtures after the *thing* they provide, not the test class. `account`, `client`, `db` — not `test_account_setup`.

## 5. Parametrizing tests

Use `@pytest.mark.parametrize` to run the same test with different inputs:

```python
import pytest

@pytest.mark.parametrize("amount,expected", [(50, 150), (0, 100), (-1, None)])
def test_deposit(account, amount, expected):
    if expected is None:
        with pytest.raises(ValueError):
            account.deposit(amount)
    else:
        account.deposit(amount)
        assert account.balance == expected
```

This is how you build a "table-driven" test suite without copy-pasting functions.

## 6. Mocking collaborators with `unittest.mock`

When a class depends on something expensive (network, file system, current time, randomness), you don't want to use the real thing in tests. `unittest.mock` (or the third-party `pytest-mock`) lets you replace collaborators with **test doubles**.

```python
from unittest.mock import Mock

def test_notifier_calls_email():
    email = Mock()                             # a fake EmailNotifier
    notifier = Notifier(email)
    notifier.send("hi")
    email.send.assert_called_once_with("hi")  # was called with "hi"
```

A `Mock` accepts any attribute access and any call, and records what happened. Use `assert_called_once_with(...)` to check exactly how it was called. Use `side_effect=[...]` or `side_effect=fn` to make a mock raise or return different values.

> **When to mock:** external services, time, randomness, the file system, anything that makes tests slow or flaky. **When not to mock:** the class under test, simple data structures, anything you can use directly.

## 7. Organizing tests

A common layout:

```
my_project/
├── my_project/
│   ├── __init__.py
│   ├── accounts.py
│   └── notifier.py
├── tests/
│   ├── __init__.py
│   ├── test_accounts.py
│   └── test_notifier.py
└── pyproject.toml
```

Keep tests outside the package. Run from the project root with `pytest`. Add a `conftest.py` for shared fixtures.

## 8. Measuring coverage

`pytest-cov` (already in our `requirements.txt`) shows what fraction of your code is exercised by tests:

```bash
pytest --cov=my_project tests/
```

A high percentage is good; 100% is rarely worth chasing. Watch the *missing* lines — they're the ones the tests didn't touch.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code

- [`code/accounts.py`](./code/accounts.py) — a `BankAccount` to test.
- [`code/test_accounts.py`](./code/test_accounts.py) — `pytest` tests using fixtures and parametrize.
- [`code/test_with_mock.py`](./code/test_with_mock.py) — using `unittest.mock.Mock` to verify collaborator calls.

## Key terms

`pytest` · assertion · `pytest.raises` · fixture · `parametrize` · `Mock` · `assert_called_once_with` · coverage

**Next →** [Module 11: Capstone](../11-capstone/)
