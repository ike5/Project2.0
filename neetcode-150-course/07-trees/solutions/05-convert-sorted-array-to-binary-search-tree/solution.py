"""Convert Sorted Array to Binary Search Tree.

NeetCode 150 — auto-generated solution.

Run:
    python solutions/05-convert-sorted-array-to-binary-search-tree/solution.py
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



def sorted_array_to_bst(nums: list[int]) -> list[int | None]:
    def build(lo, hi):
        if lo > hi: return None
        mid = (lo + hi) // 2
        node = TreeNode(nums[mid])
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node

    t = build(0, len(nums) - 1)
    return to_array(t)


def _self_test() -> None:
    assert sorted_array_to_bst([-10, -3, 0, 5, 9]) == [0, -10, 5, None, -3, None, 9], f"test 1 failed: got { sorted_array_to_bst([-10, -3, 0, 5, 9])!r } expected { [0, -10, 5, None, -3, None, 9]!r }"
    assert sorted_array_to_bst([1, 3]) == [1, None, 3], f"test 2 failed: got { sorted_array_to_bst([1, 3])!r } expected { [1, None, 3]!r }"
    print(f"all 2 tests passed for sorted_array_to_bst")


if __name__ == "__main__":
    _self_test()
