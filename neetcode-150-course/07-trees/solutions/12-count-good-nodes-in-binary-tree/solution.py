"""Count Good Nodes in Binary Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/12-count-good-nodes-in-binary-tree/solution.py
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



def good_nodes(root: list[int | None]) -> int:
    t = from_array(root)

    def dfs(node, max_so_far):
        if node is None: return 0
        good = 1 if node.val >= max_so_far else 0
        new_max = max(max_so_far, node.val)
        return good + dfs(node.left, new_max) + dfs(node.right, new_max)

    return dfs(t, float('-inf'))


def _self_test() -> None:
    assert good_nodes([3, 1, 4, 3, None, 1, 5]) == 4, f"test 1 failed: got { good_nodes([3, 1, 4, 3, None, 1, 5])!r } expected { 4!r }"
    assert good_nodes([3, 3, None, 4, 2]) == 3, f"test 2 failed: got { good_nodes([3, 3, None, 4, 2])!r } expected { 3!r }"
    print(f"all 2 tests passed for good_nodes")


if __name__ == "__main__":
    _self_test()
