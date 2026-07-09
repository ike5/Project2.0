"""pytest tests for MyCircularQueue."""

from circular_queue import MyCircularQueue


def test_basic():
    q = MyCircularQueue(3)
    assert q.enQueue(1) is True
    assert q.enQueue(2) is True
    assert q.enQueue(3) is True
    assert q.enQueue(4) is False        # full
    assert q.Rear() == 3
    assert q.isFull() is True
    assert q.deQueue() is True
    assert q.enQueue(4) is True
    assert q.Rear() == 4


def test_empty_underflow():
    q = MyCircularQueue(2)
    assert q.isEmpty() is True
    assert q.Front() == -1
    assert q.Rear() == -1
    assert q.deQueue() is False


def test_wrap_around():
    q = MyCircularQueue(2)
    q.enQueue(1)
    q.enQueue(2)
    q.deQueue()
    q.enQueue(3)
    assert q.Front() == 2
    assert q.Rear() == 3
    assert q.isFull() is True
