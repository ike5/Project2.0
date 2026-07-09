"""Kth Smallest Element in a BST.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/06-kth-smallest-element-in-a-bst/solution.py
"""

class TreeNode:
    """A minimal binary tree node."""
    def __init__(self, val: int = 0,
                 left: "TreeNode | None" = None,
                 right: "TreeNode | None" = None) -> None:
        self.val = val
        self.left = left
        self.right = right


def from_array(arr: list[int | None]) -> "TreeNode | None":
    if not arr or arr[0] is None:
        return None
    nodes: list[TreeNode | None] = [None if v is None else TreeNode(v) for v in arr]
    kids = nodes[1:]
    for parent in nodes:
        if parent is None:
            continue
        if kids:
            parent.left = kids.pop(0)
        if kids:
            parent.right = kids.pop(0)
    return nodes[0]


def to_array(node: "TreeNode | None") -> list[int | None]:
    if node is None:
        return []
    out: list[int | None] = []
    q: list[TreeNode | None] = [node]
    while q:
        n = q.pop(0)
        if n is None:
            out.append(None)
            continue
        out.append(n.val)
        q.append(n.left)
        q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out



def kth_smallest(root: list[int | None], k: int) -> int:
    t = from_array(root)
    stack: list = []
    cur = t
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        k -= 1
        if k == 0:
            return cur.val
        cur = cur.right
    return -1


def _self_test() -> None:
    assert kth_smallest([3, 1, 4, None, 2], 1) == 1, f"test 1 failed: got { kth_smallest([3, 1, 4, None, 2], 1)!r } expected { 1!r }"
    assert kth_smallest([5, 3, 6, 2, 4, None, None, 1], 3) == 3, f"test 2 failed: got { kth_smallest([5, 3, 6, 2, 4, None, None, 1], 3)!r } expected { 3!r }"
    print(f"all 2 tests passed for kth_smallest")


if __name__ == "__main__":
    _self_test()
