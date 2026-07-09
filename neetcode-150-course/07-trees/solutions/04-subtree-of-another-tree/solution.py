"""Subtree of Another Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/04-subtree-of-another-tree/solution.py
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



def is_subtree(root: list[int | None], sub: list[int | None]) -> bool:
    a = from_array(root)
    b = from_array(sub)

    def same(x, y):
        if x is None and y is None: return True
        if x is None or y is None: return False
        return x.val == y.val and same(x.left, y.left) and same(x.right, y.right)

    def walk(node):
        if node is None: return False
        if same(node, b): return True
        return walk(node.left) or walk(node.right)

    return walk(a)


def _self_test() -> None:
    assert is_subtree([3, 4, 5, 1, 2], [4, 1, 2]) == True, f"test 1 failed: got { is_subtree([3, 4, 5, 1, 2], [4, 1, 2])!r } expected { True!r }"
    assert is_subtree([3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]) == False, f"test 2 failed: got { is_subtree([3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2])!r } expected { False!r }"
    assert is_subtree([1, 1], [1]) == True, f"test 3 failed: got { is_subtree([1, 1], [1])!r } expected { True!r }"
    print(f"all 3 tests passed for is_subtree")


if __name__ == "__main__":
    _self_test()
