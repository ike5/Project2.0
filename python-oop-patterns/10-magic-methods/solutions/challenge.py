"""Reference solutions for challenge 10."""


class MyCircularQueue:
    def __init__(self, k: int) -> None:
        self.data = [0] * k
        self.head = 0
        self.count = 0
        self.cap = k

    def enQueue(self, value: int) -> bool:
        if self.isFull():
            return False
        tail = (self.head + self.count) % self.cap
        self.data[tail] = value
        self.count += 1
        return True

    def deQueue(self) -> bool:
        if self.isEmpty():
            return False
        self.head = (self.head + 1) % self.cap
        self.count -= 1
        return True

    def Front(self) -> int:
        return -1 if self.isEmpty() else self.data[self.head]

    def Rear(self) -> int:
        if self.isEmpty():
            return -1
        tail = (self.head + self.count - 1) % self.cap
        return self.data[tail]

    def isEmpty(self) -> bool:
        return self.count == 0

    def isFull(self) -> bool:
        return self.count == self.cap


class BoundedStack:
    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self._data: list[int] = []

    def push(self, x: int) -> bool:
        if len(self._data) >= self.cap:
            return False
        self._data.append(x)
        return True

    def pop(self) -> int:
        return self._data.pop()

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self):
        return iter(self._data)

    def __contains__(self, x) -> bool:
        return x in self._data

    def __getitem__(self, i):
        return self._data[i]

    def __repr__(self) -> str:
        return f"BoundedStack({self._data!r}, cap={self.cap})"
