"""Construct Binary Tree from Preorder and Inorder Traversal.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/09-construct-binary-tree-from-preorder-and-inorder-traversal/solution.py
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



def build_tree(preorder: list[int], inorder: list[int]) -> list[int | None]:
    idx = {v: i for i, v in enumerate(inorder)}
    pre_i = [0]

    def build(lo, hi):
        if lo > hi: return None
        root = TreeNode(preorder[pre_i[0]])
        pre_i[0] += 1
        mid = idx[root.val]
        root.left = build(lo, mid - 1)
        root.right = build(mid + 1, hi)
        return root

    t = build(0, len(inorder) - 1)
    return to_array(t)


def _self_test() -> None:
    assert build_tree([3, 9, 20, 15, 7], [9, 3, 15, 20, 7]) == [3, 9, 20, None, None, 15, 7], f"test 1 failed: got { build_tree([3, 9, 20, 15, 7], [9, 3, 15, 20, 7])!r } expected { [3, 9, 20, None, None, 15, 7]!r }"
    print(f"all 1 tests passed for build_tree")


if __name__ == "__main__":
    _self_test()
