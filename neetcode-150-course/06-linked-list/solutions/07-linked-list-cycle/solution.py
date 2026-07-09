"""Linked List Cycle.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/07-linked-list-cycle/solution.py
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



def has_cycle(head_vals: list[int], pos: int) -> bool:
    nodes = [ListNode(x) for x in head_vals]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]
    h = nodes[0] if nodes else None

    slow = fast = h
    while fast and fast.next:
        slow = slow.next        # type: ignore
        fast = fast.next.next   # type: ignore
        if slow is fast:
            return True
    return False


def _self_test() -> None:
    assert has_cycle([3, 2, 0, -4], 1) == True, f"test 1 failed: got { has_cycle([3, 2, 0, -4], 1)!r } expected { True!r }"
    assert has_cycle([1, 2], -1) == False, f"test 2 failed: got { has_cycle([1, 2], -1)!r } expected { False!r }"
    assert has_cycle([1], -1) == False, f"test 3 failed: got { has_cycle([1], -1)!r } expected { False!r }"
    assert has_cycle([1], 0) == True, f"test 4 failed: got { has_cycle([1], 0)!r } expected { True!r }"
    print(f"all 4 tests passed for has_cycle")


if __name__ == "__main__":
    _self_test()
