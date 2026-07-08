# Challenge 10 — Testing OOP

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Test a `Stack`.** Create `10-testing-oop/code/stack.py` with a `Stack` class that has `push(item)`, `pop() -> item`, `peek() -> item`, and `__len__`. Then create `10-testing-oop/code/test_stack.py` with at least four tests using `@pytest.fixture` for a fresh stack. Include a parametrized test for the various error cases (pop from empty stack, etc.).
2. **Mock a transport.** Create `10-testing-oop/code/mock_alert.py` with an `Alerter` class that takes a `transport` in `__init__` and has an `alert(self, msg)` method that calls `transport.send(msg)`. Write `10-testing-oop/code/test_mock_alert.py` that uses `Mock` to verify the call. Use `side_effect` to make the transport raise, and assert the exception propagates.
3. **Measure coverage on a small class.** Create `10-testing-oop/code/greeter.py` with a `Greeter` that takes a name and has `greet(formal: bool = False) -> str` (returns "Hello, Name." or "Good morning, Name."). Write `10-testing-oop/code/test_greeter.py` that covers both branches. Run `pytest --cov=10-testing-oop/code/greeter.py 10-testing-oop/code/test_greeter.py` and confirm 100% coverage.

## Success criteria

- [ ] `test_stack.py` has a fixture, at least one parametrized test, and all tests pass.
- [ ] `test_mock_alert.py` asserts `send` was called and verifies exception propagation.
- [ ] Coverage on `greeter.py` is 100% from `test_greeter.py`.
