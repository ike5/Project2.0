"""Remove Nth Node From End of List.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-remove-nth-node-from-end-of-list/solution.py
"""

class ListNode:
    """A minimal singly linked list node."""
    def __init__(self, val: int = 0, nxt: "ListNode | None" = None) -> None:
        self.val = val
        self.next = nxt
        self.random = None   # only used by the copy-random-pointer problem


def build_list(values: list[int]) -> "ListNode | None":
    head = None
    tail = None
    for v in values:
        node = ListNode(v)
        if head is None:
            head = node
            tail = node
        else:
            tail.next = node  # type: ignore
            tail = node
    return head


def to_array_list(head: "ListNode | None") -> list[int]:
    out: list[int] = []
    while head is not None:
        out.append(head.val)
        head = head.next  # type: ignore
    return out



def remove_nth_from_end(head: list[int], n: int) -> list[int]:
    nodes = [ListNode(x) for x in head]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    h = nodes[0] if nodes else None

    dummy = ListNode(0)
    dummy.next = h
    slow = dummy
    fast = dummy
    for _ in range(n):
        fast = fast.next   # type: ignore
    while fast.next:       # type: ignore
        slow = slow.next   # type: ignore
        fast = fast.next   # type: ignore
    slow.next = slow.next.next  # type: ignore

    out: list[int] = []
    n2 = dummy.next
    while n2:
        out.append(n2.val); n2 = n2.next
    return out


def _self_test() -> None:
    assert remove_nth_from_end([1, 2, 3, 4, 5], 2) == [1, 2, 3, 5], f"test 1 failed: got { remove_nth_from_end([1, 2, 3, 4, 5], 2)!r } expected { [1, 2, 3, 5]!r }"
    assert remove_nth_from_end([1], 1) == [], f"test 2 failed: got { remove_nth_from_end([1], 1)!r } expected { []!r }"
    assert remove_nth_from_end([1, 2], 1) == [1], f"test 3 failed: got { remove_nth_from_end([1, 2], 1)!r } expected { [1]!r }"
    print(f"all 3 tests passed for remove_nth_from_end")


if __name__ == "__main__":
    _self_test()
