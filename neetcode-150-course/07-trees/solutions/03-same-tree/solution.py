"""Same Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/03-same-tree/solution.py
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



def is_same_tree(p: list[int | None], q: list[int | None]) -> bool:
    a = from_array(p)
    b = from_array(q)

    def same(x, y):
        if x is None and y is None:
            return True
        if x is None or y is None:
            return False
        return x.val == y.val and same(x.left, y.left) and same(x.right, y.right)

    return same(a, b)


def _self_test() -> None:
    assert is_same_tree([1, 2, 3], [1, 2, 3]) == True, f"test 1 failed: got { is_same_tree([1, 2, 3], [1, 2, 3])!r } expected { True!r }"
    assert is_same_tree([1, 2], [1, None, 2]) == False, f"test 2 failed: got { is_same_tree([1, 2], [1, None, 2])!r } expected { False!r }"
    assert is_same_tree([], []) == True, f"test 3 failed: got { is_same_tree([], [])!r } expected { True!r }"
    print(f"all 3 tests passed for is_same_tree")


if __name__ == "__main__":
    _self_test()
