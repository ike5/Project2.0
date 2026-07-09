"""Serialize and Deserialize Binary Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/14-serialize-and-deserialize-binary-tree/solution.py
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



def serialize(root: list[int | None]) -> str:
    t = from_array(root)
    out: list[str] = []

    def dfs(node):
        if node is None:
            out.append('null')
            return
        out.append(str(node.val))
        dfs(node.left)
        dfs(node.right)

    dfs(t)
    return ','.join(out)


def _self_test() -> None:
    assert serialize([1, 2, 3, None, None, 4, 5]) == '1,2,null,null,3,4,null,null,5,null,null', f"test 1 failed: got { serialize([1, 2, 3, None, None, 4, 5])!r } expected { '1,2,null,null,3,4,null,null,5,null,null'!r }"
    print(f"all 1 tests passed for serialize")


if __name__ == "__main__":
    _self_test()
