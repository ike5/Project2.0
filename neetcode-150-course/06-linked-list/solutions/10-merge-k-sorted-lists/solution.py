"""Merge K Sorted Lists.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/10-merge-k-sorted-lists/solution.py
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



def merge_k_lists(lists: list[list[int]]) -> list[int]:
    import heapq
    heap: list[tuple[int, int, ListNode]] = []
    for i, lst in enumerate(lists):
        n = build_list(lst)
        if n:
            heapq.heappush(heap, (n.val, i, n))
    dummy = ListNode(0)
    tail = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = tail.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    out: list[int] = []
    n = dummy.next
    while n:
        out.append(n.val); n = n.next
    return out


def _self_test() -> None:
    assert merge_k_lists([[1, 4, 5], [1, 3, 4], [2, 6]]) == [1, 1, 2, 3, 4, 4, 5, 6], f"test 1 failed: got { merge_k_lists([[1, 4, 5], [1, 3, 4], [2, 6]])!r } expected { [1, 1, 2, 3, 4, 4, 5, 6]!r }"
    assert merge_k_lists([[]]) == [], f"test 2 failed: got { merge_k_lists([[]])!r } expected { []!r }"
    assert merge_k_lists([]) == [], f"test 3 failed: got { merge_k_lists([])!r } expected { []!r }"
    print(f"all 3 tests passed for merge_k_lists")


if __name__ == "__main__":
    _self_test()
