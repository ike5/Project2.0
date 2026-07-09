"""pytest tests for MyLinkedList."""

from linked_list import MyLinkedList


def test_from_array():
    ll = MyLinkedList.from_array([1, 2, 3])
    assert ll.get(0) == 1
    assert ll.get(1) == 2
    assert ll.get(2) == 3
    assert ll.get(3) == -1


def test_add_at_head_and_tail():
    ll = MyLinkedList()
    ll.addAtHead(2)
    ll.addAtHead(1)
    ll.addAtTail(3)
    assert ll.get(0) == 1
    assert ll.get(2) == 3


def test_add_at_index():
    ll = MyLinkedList.from_array([1, 3])
    ll.addAtIndex(1, 2)
    assert ll.get(0) == 1
    assert ll.get(1) == 2
    assert ll.get(2) == 3


def test_delete():
    ll = MyLinkedList.from_array([1, 2, 3])
    ll.deleteAtIndex(1)
    assert ll.get(0) == 1
    assert ll.get(1) == 3
    assert ll.get(2) == -1


def test_out_of_range():
    ll = MyLinkedList()
    assert ll.get(0) == -1
    ll.addAtIndex(-1, 0)         # no-op
    ll.addAtIndex(1, 0)          # no-op
    assert ll.get(0) == -1
