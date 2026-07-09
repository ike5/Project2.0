"""Reverse Linked List.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-reverse-linked-list/solution.py
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



def reverse_list(head: list[int]) -> list[int]:
    # 'head' is given as a list of ints; convert to nodes, reverse, convert back
    nodes = [ListNode(x) for x in head]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    head_node = nodes[0] if nodes else None

    prev = None
    curr = head_node
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    new_head = prev

    # convert back to list
    out: list[int] = []
    while new_head:
        out.append(new_head.val)
        new_head = new_head.next
    return out


def _self_test() -> None:
    assert reverse_list([1, 2, 3, 4, 5]) == [5, 4, 3, 2, 1], f"test 1 failed: got { reverse_list([1, 2, 3, 4, 5])!r } expected { [5, 4, 3, 2, 1]!r }"
    assert reverse_list([1, 2]) == [2, 1], f"test 2 failed: got { reverse_list([1, 2])!r } expected { [2, 1]!r }"
    assert reverse_list([]) == [], f"test 3 failed: got { reverse_list([])!r } expected { []!r }"
    print(f"all 3 tests passed for reverse_list")


if __name__ == "__main__":
    _self_test()
