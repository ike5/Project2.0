"""Binary Tree Maximum Path Sum.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/15-binary-tree-maximum-path-sum/solution.py
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



def max_path_sum(root: list[int | None]) -> int:
    t = from_array(root)
    best = [float('-inf')]

    def gain(node):
        if node is None: return 0
        left = max(0, gain(node.left))
        right = max(0, gain(node.right))
        best[0] = max(best[0], node.val + left + right)
        return node.val + max(left, right)

    gain(t)
    return best[0]


def _self_test() -> None:
    assert max_path_sum([1, 2, 3]) == 6, f"test 1 failed: got { max_path_sum([1, 2, 3])!r } expected { 6!r }"
    assert max_path_sum([-10, 9, 20, None, None, 15, 7]) == 42, f"test 2 failed: got { max_path_sum([-10, 9, 20, None, None, 15, 7])!r } expected { 42!r }"
    assert max_path_sum([-3]) == -3, f"test 3 failed: got { max_path_sum([-3])!r } expected { -3!r }"
    print(f"all 3 tests passed for max_path_sum")


if __name__ == "__main__":
    _self_test()
