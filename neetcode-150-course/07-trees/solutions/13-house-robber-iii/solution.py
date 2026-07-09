"""House Robber III.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/13-house-robber-iii/solution.py
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



def rob_tree(root: list[int | None]) -> int:
    t = from_array(root)

    def dfs(node):
        if node is None: return (0, 0)
        lr, ls = dfs(node.left)
        rr, rs = dfs(node.right)
        rob = node.val + ls + rs
        skip = max(lr, ls) + max(rr, rs)
        return (rob, skip)

    return max(dfs(t))


def _self_test() -> None:
    assert rob_tree([3, 2, 3, None, 3, None, 1]) == 7, f"test 1 failed: got { rob_tree([3, 2, 3, None, 3, None, 1])!r } expected { 7!r }"
    assert rob_tree([3, 4, 5, 1, 3, None, 1]) == 9, f"test 2 failed: got { rob_tree([3, 4, 5, 1, 3, None, 1])!r } expected { 9!r }"
    print(f"all 2 tests passed for rob_tree")


if __name__ == "__main__":
    _self_test()
