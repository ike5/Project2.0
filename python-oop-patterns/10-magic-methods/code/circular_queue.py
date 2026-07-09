"""LeetCode 622 — Design Circular Queue.

Run me: python 10-magic-methods/code/circular_queue.py
"""


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


def main() -> None:
    q: MyCircularQueue = MyCircularQueue(3)
    print(q.enQueue(1))    # True
    print(q.enQueue(2))    # True
    print(q.enQueue(3))    # True
    print(q.enQueue(4))    # False
    print(q.Rear())        # 3
    print(q.isFull())      # True
    print(q.deQueue())     # True
    print(q.enQueue(4))    # True
    print(q.Rear())        # 4


if __name__ == "__main__":
    main()
