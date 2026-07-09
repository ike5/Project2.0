"""Reverse Nodes in k-Group.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/11-reverse-nodes-in-k-group/solution.py
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



def reverse_k_group(head: list[int], k: int) -> list[int]:
    nodes = [ListNode(x) for x in head]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    h = nodes[0] if nodes else None

    def reverse_k(start, k):
        # returns (new_head, next_after_group)
        prev = None
        curr = start
        for _ in range(k):
            nxt = curr.next   # type: ignore
            curr.next = prev  # type: ignore
            prev = curr
            curr = nxt
        return prev, curr

    dummy = ListNode(0)
    dummy.next = h
    group_prev = dummy
    while True:
        kth = group_prev
        for _ in range(k):
            kth = kth.next    # type: ignore
            if kth is None:
                # fewer than k remain; we're done
                out: list[int] = []
                n = dummy.next
                while n:
                    out.append(n.val); n = n.next
                return out
        group_next = kth.next
        # reverse
        new_head, _ = reverse_k(group_prev.next, k)  # type: ignore
        # reconnect
        group_prev.next = new_head  # type: ignore
        # find the new tail
        new_tail = new_head
        while new_tail.next:    # type: ignore
            new_tail = new_tail.next  # type: ignore
        new_tail.next = group_next  # type: ignore
        group_prev = new_tail

    # unreachable
    return []


def _self_test() -> None:
    assert reverse_k_group([1, 2, 3, 4, 5], 2) == [2, 1, 4, 3, 5], f"test 1 failed: got { reverse_k_group([1, 2, 3, 4, 5], 2)!r } expected { [2, 1, 4, 3, 5]!r }"
    assert reverse_k_group([1, 2, 3, 4, 5], 3) == [3, 2, 1, 4, 5], f"test 2 failed: got { reverse_k_group([1, 2, 3, 4, 5], 3)!r } expected { [3, 2, 1, 4, 5]!r }"
    print(f"all 2 tests passed for reverse_k_group")


if __name__ == "__main__":
    _self_test()
