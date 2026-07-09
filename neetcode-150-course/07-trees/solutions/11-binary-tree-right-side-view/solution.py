"""Binary Tree Right Side View.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/11-binary-tree-right-side-view/solution.py
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



def right_side_view(root: list[int | None]) -> list[int]:
    t = from_array(root)
    if t is None: return []
    out: list[int] = []
    q = [t]
    while q:
        for i in range(len(q)):
            n = q.pop(0)
            if i == len(q):  # after pop, original-size - 1 - i was 0
                pass
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
        # wrong logic above; redo: record rightmost BEFORE popping children
    # corrected version:
    out = []
    q = [t]
    while q:
        sz = len(q)
        for i in range(sz):
            n = q.pop(0)
            if i == sz - 1:
                out.append(n.val)
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
    return out


def _self_test() -> None:
    assert right_side_view([1, 2, 3, None, 5, None, 4]) == [1, 3, 4], f"test 1 failed: got { right_side_view([1, 2, 3, None, 5, None, 4])!r } expected { [1, 3, 4]!r }"
    assert right_side_view([1, None, 3]) == [1, 3], f"test 2 failed: got { right_side_view([1, None, 3])!r } expected { [1, 3]!r }"
    print(f"all 2 tests passed for right_side_view")


if __name__ == "__main__":
    _self_test()
