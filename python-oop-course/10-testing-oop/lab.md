# Lab 10 — Testing OOP

**You'll:** run a small test suite, see fixtures and parametrize in action, and try mocking. ⏱️ ~30 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Run the existing test file

```bash
pytest 10-testing-oop/code/test_accounts.py -v
```

✅ You should see all the tests pass and a coverage-like report (if you ran with `--cov`).

## Part B — Watch a test fail

Open `test_accounts.py`, change an expected value, and run the test again. See the failure output. Then change it back.

## Part C — Try the mock example

```bash
pytest 10-testing-oop/code/test_with_mock.py -v
```

✅ You should see the test pass — the mock recorded the call we asserted on.

## Part D — Coverage

```bash
pytest --cov=10-testing-oop/code/accounts.py 10-testing-oop/code/test_accounts.py
```

✅ You should see a coverage report showing the `BankAccount` methods you exercised.

## Cleanup

Nothing to clean up.

## What you learned

- `pytest` finds files named `test_*.py` and functions named `test_*`.
- `@pytest.fixture` shares setup across tests, fresh per test by default.
- `@pytest.mark.parametrize` runs one test with many input sets.
- `unittest.mock.Mock` stands in for collaborators; `assert_called_once_with(...)` checks calls.
- `pytest --cov=...` measures which lines your tests executed.

➡️ **[challenge.md](./challenge.md)** then [Module 11: Capstone](../11-capstone/).
