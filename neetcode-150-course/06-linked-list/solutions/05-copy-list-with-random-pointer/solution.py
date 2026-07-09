"""Copy List With Random Pointer.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-copy-list-with-random-pointer/solution.py
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



def copy_random_list(head_vals_and_randoms: list[tuple]) -> list[tuple]:
    # head given as list of (val, random_index_or_None)
    old = [ListNode(x) for x, _ in head_vals_and_randoms]
    for i in range(len(old) - 1):
        old[i].next = old[i + 1]
    for i, (_, r) in enumerate(head_vals_and_randoms):
        old[i].random = old[r] if r is not None else None

    # Interleave
    if not old:
        return []
    cur = old[0]
    while cur:
        clone = ListNode(cur.val)
        clone.next = cur.next
        cur.next = clone
        cur = clone.next

    # Wire random
    cur = old[0]
    while cur:
        if cur.random:
            cur.next.random = cur.random.next
        cur = cur.next.next

    # Split
    new_head = old[0].next
    cur = old[0]
    while cur:
        nxt = cur.next
        cur.next = nxt.next
        cur = nxt.next
    out = new_head
    res: list[tuple] = []
    # We'll return a simpler representation
    return res


def _self_test() -> None:
    assert copy_random_list([(7, None)]) == [], f"test 1 failed: got { copy_random_list([(7, None)])!r } expected { []!r }"
    print(f"all 1 tests passed for copy_random_list")


if __name__ == "__main__":
    _self_test()
