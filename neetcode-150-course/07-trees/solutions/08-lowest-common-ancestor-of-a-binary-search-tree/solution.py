"""Lowest Common Ancestor of a Binary Search Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/08-lowest-common-ancestor-of-a-binary-search-tree/solution.py
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



def lowest_common_ancestor_bst(root: list[int | None], p: int, q: int) -> int:
    t = from_array(root)
    cur = t
    while cur:
        if p < cur.val and q < cur.val:
            cur = cur.left
        elif p > cur.val and q > cur.val:
            cur = cur.right
        else:
            return cur.val
    return -1


def _self_test() -> None:
    assert lowest_common_ancestor_bst([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8) == 6, f"test 1 failed: got { lowest_common_ancestor_bst([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8)!r } expected { 6!r }"
    assert lowest_common_ancestor_bst([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4) == 2, f"test 2 failed: got { lowest_common_ancestor_bst([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4)!r } expected { 2!r }"
    print(f"all 2 tests passed for lowest_common_ancestor_bst")


if __name__ == "__main__":
    _self_test()
