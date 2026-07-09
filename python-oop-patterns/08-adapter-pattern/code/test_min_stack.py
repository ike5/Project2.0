"""pytest tests for MinStack (parallel-list variant)."""

from min_stack import MinStack


def test_basic():
    s = MinStack()
    s.push(-2)
    s.push(0)
    s.push(-3)
    assert s.getMin() == -3
    s.pop()
    assert s.top() == 0
    assert s.getMin() == -2


def test_increasing():
    s = MinStack()
    for v in (1, 2, 3, 4, 5):
        s.push(v)
    assert s.getMin() == 1
    assert s.top() == 5


def test_decreasing():
    s = MinStack()
    for v in (5, 4, 3, 2, 1):
        s.push(v)
    assert s.getMin() == 1
    s.pop()                # removes 1, stack=[5,4,3,2], min=2
    assert s.getMin() == 2
    s.pop()                # removes 2, stack=[5,4,3], min=3
    s.pop()                # removes 3, stack=[5,4], min=4
    assert s.getMin() == 4
    assert s.top() == 4


def test_duplicates():
    s = MinStack()
    s.push(0)
    s.push(1)
    s.push(0)
    assert s.getMin() == 0
    s.pop()
    assert s.getMin() == 0
