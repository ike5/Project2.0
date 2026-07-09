"""Add Two Numbers.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-add-two-numbers/solution.py
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



def add_two_numbers(a: list[int], b: list[int]) -> list[int]:
    l1 = build_list(a)
    l2 = build_list(b)
    dummy = ListNode(0)
    tail = dummy
    carry = 0
    while l1 or l2 or carry:
        s = carry
        if l1:
            s += l1.val; l1 = l1.next
        if l2:
            s += l2.val; l2 = l2.next
        carry, digit = divmod(s, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    out: list[int] = []
    n = dummy.next
    while n:
        out.append(n.val); n = n.next
    return out


def _self_test() -> None:
    assert add_two_numbers([2, 4, 3], [5, 6, 4]) == [7, 0, 8], f"test 1 failed: got { add_two_numbers([2, 4, 3], [5, 6, 4])!r } expected { [7, 0, 8]!r }"
    assert add_two_numbers([0], [0]) == [0], f"test 2 failed: got { add_two_numbers([0], [0])!r } expected { [0]!r }"
    assert add_two_numbers([9, 9, 9, 9], [9, 9, 9, 9, 9, 9, 9]) == [8, 9, 9, 9, 0, 0, 0, 1], f"test 3 failed: got { add_two_numbers([9, 9, 9, 9], [9, 9, 9, 9, 9, 9, 9])!r } expected { [8, 9, 9, 9, 0, 0, 0, 1]!r }"
    print(f"all 3 tests passed for add_two_numbers")


if __name__ == "__main__":
    _self_test()
