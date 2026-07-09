"""Invert Binary Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/01-invert-binary-tree/solution.py
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



def invert_tree(root: list[int | None]) -> list[int | None]:
    # 'root' is a level-order array (nulls allowed)
    def from_array(arr: list[int | None]):
        if not arr or arr[0] is None:
            return None
        nodes = [None if v is None else TreeNode(v) for v in arr]
        kids = nodes[1:]
        for parent in nodes:
            if parent is None:
                continue
            left = kids.pop(0) if kids else None
            right = kids.pop(0) if kids else None
            parent.left = left
            parent.right = right
        return nodes[0]

    def to_array(node):
        if node is None:
            return []
        out: list[int | None] = []
        q = [node]
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

    t = from_array(root)
    def invert(node):
        if node is None:
            return None
        node.left, node.right = invert(node.right), invert(node.left)
        return node
    return to_array(invert(t))


def _self_test() -> None:
    assert invert_tree([4, 2, 7, 1, 3, 6, 9]) == [4, 7, 2, 9, 6, 3, 1], f"test 1 failed: got { invert_tree([4, 2, 7, 1, 3, 6, 9])!r } expected { [4, 7, 2, 9, 6, 3, 1]!r }"
    assert invert_tree([2, 1, 3]) == [2, 3, 1], f"test 2 failed: got { invert_tree([2, 1, 3])!r } expected { [2, 3, 1]!r }"
    assert invert_tree([]) == [], f"test 3 failed: got { invert_tree([])!r } expected { []!r }"
    print(f"all 3 tests passed for invert_tree")


if __name__ == "__main__":
    _self_test()
