"""Merge Two Sorted Lists.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-merge-two-sorted-lists/solution.py
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



def merge_two_lists(a: list[int], b: list[int]) -> list[int]:
    # 'a' and 'b' are given as lists of ints
    list1 = build_list(a)
    list2 = build_list(b)

    dummy = ListNode(0)
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list1 or list2

    # convert to list
    out: list[int] = []
    n = dummy.next
    while n:
        out.append(n.val)
        n = n.next
    return out


def _self_test() -> None:
    assert merge_two_lists([1, 2, 4], [1, 3, 4]) == [1, 1, 2, 3, 4, 4], f"test 1 failed: got { merge_two_lists([1, 2, 4], [1, 3, 4])!r } expected { [1, 1, 2, 3, 4, 4]!r }"
    assert merge_two_lists([], []) == [], f"test 2 failed: got { merge_two_lists([], [])!r } expected { []!r }"
    assert merge_two_lists([], [0]) == [0], f"test 3 failed: got { merge_two_lists([], [0])!r } expected { [0]!r }"
    print(f"all 3 tests passed for merge_two_lists")


if __name__ == "__main__":
    _self_test()
