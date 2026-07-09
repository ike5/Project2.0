"""Maximum Depth of Binary Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/02-maximum-depth-of-binary-tree/solution.py
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



def max_depth(root: list[int | None]) -> int:
    t = from_array(root)

    def depth(node):
        if node is None:
            return 0
        return 1 + max(depth(node.left), depth(node.right))

    return depth(t)


def _self_test() -> None:
    assert max_depth([3, 9, 20, None, None, 15, 7]) == 3, f"test 1 failed: got { max_depth([3, 9, 20, None, None, 15, 7])!r } expected { 3!r }"
    assert max_depth([1, None, 2]) == 2, f"test 2 failed: got { max_depth([1, None, 2])!r } expected { 2!r }"
    assert max_depth([]) == 0, f"test 3 failed: got { max_depth([])!r } expected { 0!r }"
    assert max_depth([1]) == 1, f"test 4 failed: got { max_depth([1])!r } expected { 1!r }"
    print(f"all 4 tests passed for max_depth")


if __name__ == "__main__":
    _self_test()
