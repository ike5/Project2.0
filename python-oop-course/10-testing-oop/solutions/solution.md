# Solution 10 — Testing OOP

Reference answers. Try first.

## Key points

### Task 1 — `stack.py` and `test_stack.py`

```python
# 10-testing-oop/code/stack.py
"""A small Stack class to test.

Run tests:
    pytest 10-testing-oop/code/test_stack.py -v
"""


class Stack:
    def __init__(self) -> None:
        self._items: list = []

    def push(self, item) -> None:
        self._items.append(item)

    def pop(self):
        if not self._items:
            raise IndexError("pop from empty stack")
        return self._items.pop()

    def peek(self):
        if not self._items:
            raise IndexError("peek from empty stack")
        return self._items[-1]

    def __len__(self) -> int:
        return len(self._items)
```

```python
# 10-testing-oop/code/test_stack.py
import pytest

from stack import Stack


@pytest.fixture
def s():
    return Stack()


def test_new_stack_is_empty(s):
    assert len(s) == 0


def test_push_increases_length(s):
    s.push(1)
    s.push(2)
    assert len(s) == 2


def test_pop_returns_last_pushed(s):
    s.push("a")
    s.push("b")
    assert s.pop() == "b"
    assert len(s) == 1


def test_peek_returns_top_without_popping(s):
    s.push("a")
    assert s.peek() == "a"
    assert len(s) == 1


@pytest.mark.parametrize("method_name", ["pop", "peek"])
def test_empty_stack_raises(s, method_name):
    method = getattr(s, method_name)
    with pytest.raises(IndexError):
        method()
```

### Task 2 — `mock_alert.py` and `test_mock_alert.py`

```python
# 10-testing-oop/code/mock_alert.py
class Alerter:
    def __init__(self, transport) -> None:
        self.transport = transport

    def alert(self, msg: str) -> None:
        self.transport.send(msg)
```

```python
# 10-testing-oop/code/test_mock_alert.py
from unittest.mock import Mock

import pytest

from mock_alert import Alerter


def test_alert_calls_transport_with_message():
    transport = Mock()
    Alerter(transport).alert("hi")
    transport.send.assert_called_once_with("hi")


def test_transport_exception_propagates():
    transport = Mock()
    transport.send.side_effect = RuntimeError("down")
    with pytest.raises(RuntimeError, match="down"):
        Alerter(transport).alert("hi")
```

### Task 3 — `greeter.py` and `test_greeter.py`

```python
# 10-testing-oop/code/greeter.py
class Greeter:
    def __init__(self, name: str) -> None:
        self.name = name

    def greet(self, formal: bool = False) -> str:
        if formal:
            return f"Good morning, {self.name}."
        return f"Hello, {self.name}."
```

```python
# 10-testing-oop/code/test_greeter.py
from greeter import Greeter


def test_casual_greeting():
    assert Greeter("Ana").greet() == "Hello, Ana."


def test_formal_greeting():
    assert Greeter("Ana").greet(formal=True) == "Good morning, Ana."
```

Coverage command:
```bash
pytest --cov=10-testing-oop/code/greeter 10-testing-oop/code/test_greeter.py
```

## Common pitfalls

- **Putting a fixture in a class and forgetting `@pytest.fixture` on the method.** `pytest` only treats it as a fixture if it's decorated (or in `conftest.py`).
- **Asserting on `repr` strings.** They change between Python versions. Test public behavior.
- **Mocking the class under test.** You'll just be testing the mock. Mock *collaborators*.
- **Going for 100% coverage on code that doesn't matter.** Cover the meaningful branches, not every line of an error-message string.
