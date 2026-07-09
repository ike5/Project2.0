"""Binary Tree Level Order Traversal.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/10-binary-tree-level-order-traversal/solution.py
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



def level_order(root: list[int | None]) -> list[list[int]]:
    t = from_array(root)
    if t is None: return []
    out: list[list[int]] = []
    q = [t]
    while q:
        level: list[int] = []
        for _ in range(len(q)):
            n = q.pop(0)
            level.append(n.val)
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
        out.append(level)
    return out


def _self_test() -> None:
    assert sorted([sorted(g) for g in level_order([3, 9, 20, None, None, 15, 7])]) == sorted([sorted(g) for g in [[3], [9, 20], [15, 7]]]), f"test 1 failed: got { sorted([sorted(g) for g in level_order([3, 9, 20, None, None, 15, 7])])!r } expected { sorted([sorted(g) for g in [[3], [9, 20], [15, 7]]])!r }"
    assert sorted([sorted(g) for g in level_order([1])]) == sorted([sorted(g) for g in [[1]]]), f"test 2 failed: got { sorted([sorted(g) for g in level_order([1])])!r } expected { sorted([sorted(g) for g in [[1]]])!r }"
    print(f"all 2 tests passed for level_order")


if __name__ == "__main__":
    _self_test()
