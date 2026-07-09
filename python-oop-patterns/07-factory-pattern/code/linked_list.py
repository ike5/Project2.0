"""LeetCode 707 — Design Linked List, with a from_array factory.

Run me: python 07-factory-pattern/code/linked_list.py
"""


class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None) -> None:
        self.val = val
        self.next = next


class MyLinkedList:
    def __init__(self) -> None:
        self.head: ListNode = ListNode()   # sentinel
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
            cur = cur.next            # type: ignore[union-attr]
        return cur.val                # type: ignore[union-attr]

    def addAtHead(self, val: int) -> None:
        self.addAtIndex(0, val)

    def addAtTail(self, val: int) -> None:
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index < 0 or index > self.size:
            return
        cur = self.head
        for _ in range(index):
            cur = cur.next            # type: ignore[assignment]
        cur.next = ListNode(val, cur.next)
        self.size += 1

    def deleteAtIndex(self, index: int) -> None:
        if index < 0 or index >= self.size:
            return
        cur = self.head
        for _ in range(index):
            cur = cur.next            # type: ignore[assignment]
        cur.next = cur.next.next      # type: ignore[union-attr]
        self.size -= 1

    def __repr__(self) -> str:
        vals = []
        cur = self.head.next
        while cur is not None:
            vals.append(cur.val)
            cur = cur.next
        return f"MyLinkedList({vals})"


def main() -> None:
    ll = MyLinkedList.from_array([1, 2, 3])
    print(ll)
    print("get(1) =", ll.get(1))         # 2
    ll.addAtHead(0)
    print("after addAtHead(0):", ll)
    ll.deleteAtIndex(1)
    print("after deleteAtIndex(1):", ll)
    print("get(1) =", ll.get(1))         # 2 -> was 1, now 2


if __name__ == "__main__":
    main()
