"""Reorder List.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-reorder-list/solution.py
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



def reorder_list(head: list[int]) -> list[int]:
    nodes = [ListNode(x) for x in head]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    h = nodes[0] if nodes else None
    if h is None or h.next is None:
        result: list[int] = []
        n = h
        while n:
            result.append(n.val); n = n.next
        return result

    # 1) find middle
    slow, fast = h, h
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    second = slow.next
    slow.next = None

    # 2) reverse second
    prev = None
    curr = second
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    second = prev

    # 3) interleave
    first = h
    while second:
        tmp1, tmp2 = first.next, second.next
        first.next = second
        second.next = tmp1
        first, second = tmp1, tmp2

    # to list
    out: list[int] = []
    n = h
    while n:
        out.append(n.val); n = n.next
    return out


def _self_test() -> None:
    assert reorder_list([1, 2, 3, 4]) == [1, 4, 2, 3], f"test 1 failed: got { reorder_list([1, 2, 3, 4])!r } expected { [1, 4, 2, 3]!r }"
    assert reorder_list([1, 2, 3, 4, 5]) == [1, 5, 2, 4, 3], f"test 2 failed: got { reorder_list([1, 2, 3, 4, 5])!r } expected { [1, 5, 2, 4, 3]!r }"
    print(f"all 2 tests passed for reorder_list")


if __name__ == "__main__":
    _self_test()
