"""Reference solutions for challenge 07."""

import math
from typing import Any


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None) -> None:
        self.val = val
        self.next = next


class MyLinkedList:
    def __init__(self) -> None:
        self.head: ListNode = ListNode()
        self.size = 0

    @classmethod
    def from_array(cls, xs: list[int]) -> "MyLinkedList":
        ll = cls()
        for x in xs:
            ll.addAtTail(x)
        return ll

    def get(self, index: int) -> int:
        if index < 0 or index >= self.size:
            return -1
        cur = self.head.next
        for _ in range(index):
            cur = cur.next  # type: ignore[union-attr]
        return cur.val      # type: ignore[union-attr]

    def addAtHead(self, val: int) -> None:
        self.addAtIndex(0, val)

    def addAtTail(self, val: int) -> None:
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index < 0 or index > self.size:
            return
        cur = self.head
        for _ in range(index):
            cur = cur.next  # type: ignore[assignment]
        cur.next = ListNode(val, cur.next)
        self.size += 1

    def deleteAtIndex(self, index: int) -> None:
        if index < 0 or index >= self.size:
            return
        cur = self.head
        for _ in range(index):
            cur = cur.next  # type: ignore[assignment]
        cur.next = cur.next.next  # type: ignore[union-attr]
        self.size -= 1


class Shape:
    def area(self) -> float:
        raise NotImplementedError

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Shape":
        kind = d["kind"]
        if kind == "square":
            return Square(d["side"])
        if kind == "circle":
            return Circle(d["radius"])
        if kind == "rectangle":
            return Rectangle(d["w"], d["h"])
        if kind == "triangle":
            return Triangle(d["base"], d["height"])
        raise ValueError(f"unknown shape: {kind}")


class Square(Shape):
    def __init__(self, side: float) -> None:
        self.side = side

    def area(self) -> float:
        return self.side * self.side


class Circle(Shape):
    def __init__(self, radius: float) -> None:
        self.radius = radius

    def area(self) -> float:
        return math.pi * self.radius ** 2


class Rectangle(Shape):
    def __init__(self, w: float, h: float) -> None:
        self.w, self.h = w, h

    def area(self) -> float:
        return self.w * self.h


class Triangle(Shape):
    def __init__(self, base: float, height: float) -> None:
        self.base, self.height = base, height

    def area(self) -> float:
        return 0.5 * self.base * self.height
