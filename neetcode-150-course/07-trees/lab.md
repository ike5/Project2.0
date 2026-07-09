# Lab 07 — Trees

**You'll:** implement *Invert Binary Tree* and *Maximum Depth* in both
languages, getting comfortable with tree recursion and the helper utilities
for converting between arrays and `TreeNode` trees. ⏱️ ~1.5 h.

---

## Part A — *Invert Binary Tree* in Python

Create `07-trees/lab_invert.py`:

```python
class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def from_array(arr):
    if not arr or arr[0] is None:
        return None
    nodes = [None if v is None else TreeNode(v) for v in arr]
    kids = nodes[1:]
    for parent in nodes:
        if parent is None:
            continue
        if kids: parent.left = kids.pop(0)
        if kids: parent.right = kids.pop(0)
    return nodes[0]


def to_array(node):
    if node is None:
        return []
    out, q = [], [node]
    while q:
        n = q.pop(0)
        if n is None:
            out.append(None); continue
        out.append(n.val)
        q.append(n.left); q.append(n.right)
    while out and out[-1] is None:
        out.pop()
    return out


def invert_tree(root):
    # your code
    ...


if __name__ == "__main__":
    assert to_array(invert_tree(from_array([4, 2, 7, 1, 3, 6, 9]))) == [4, 7, 2, 9, 6, 3, 1]
    assert to_array(invert_tree(from_array([2, 1, 3]))) == [2, 3, 1]
    assert to_array(invert_tree(from_array([]))) == []
    print("all tests passed")
```

**Walk-through:** recursive swap.

```python
def invert_tree(root):
    if root is None:
        return None
    root.left, root.right = invert_tree(root.right), invert_tree(root.left)
    return root
```

We save `root.left` and `root.right` on the right-hand side of the
assignment so we don't lose them when we overwrite.

✅ Run it.

## Part B — *Invert Binary Tree* in Java 21

```java
public class LabInvert {
    public static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int v) { val = v; }
    }

    public static TreeNode fromArray(Integer[] arr) {
        if (arr == null || arr.length == 0 || arr[0] == null) return null;
        TreeNode[] nodes = new TreeNode[arr.length];
        for (int i = 0; i < arr.length; i++) if (arr[i] != null) nodes[i] = new TreeNode(arr[i]);
        java.util.List<TreeNode> kids = new java.util.ArrayList<>();
        for (int i = 1; i < arr.length; i++) kids.add(nodes[i]);
        for (TreeNode parent : nodes) {
            if (parent == null) continue;
            if (!kids.isEmpty()) parent.left = kids.remove(0);
            if (!kids.isEmpty()) parent.right = kids.remove(0);
        }
        return nodes[0];
    }

    public static Integer[] toArray(TreeNode node) {
        if (node == null) return new Integer[0];
        java.util.List<Integer> out = new java.util.ArrayList<>();
        java.util.List<TreeNode> q = new java.util.ArrayList<>();
        q.add(node);
        while (!q.isEmpty()) {
            TreeNode n = q.remove(0);
            if (n == null) { out.add(null); continue; }
            out.add(n.val);
            q.add(n.left); q.add(n.right);
        }
        while (!out.isEmpty() && out.get(out.size() - 1) == null) out.remove(out.size() - 1);
        return out.toArray(new Integer[0]);
    }

    public static TreeNode invertTree(TreeNode root) {
        // your code
    }

    public static void main(String[] args) {
        assert java.util.Arrays.equals(
            toArray(invertTree(fromArray(new Integer[]{4, 2, 7, 1, 3, 6, 9}))),
            new Integer[]{4, 7, 2, 9, 6, 3, 1}
        );
        assert java.util.Arrays.equals(
            toArray(invertTree(fromArray(new Integer[]{2, 1, 3}))),
            new Integer[]{2, 3, 1}
        );
        assert java.util.Arrays.equals(
            toArray(invertTree(fromArray(new Integer[]{}))),
            new Integer[]{}
        );
        System.out.println("all tests passed");
    }
}
```

**Walk-through:**

```java
public static TreeNode invertTree(TreeNode root) {
    if (root == null) return null;
    TreeNode tmp = root.left;
    root.left = invertTree(root.right);
    root.right = invertTree(tmp);
    return root;
}
```

The `tmp` save is critical: after `root.left = invertTree(root.right)`,
`root.left` no longer points to the original left subtree. We saved it
in `tmp` so we can recurse on it next.

## Part C — *Maximum Depth* in Python

```python
def max_depth(root):
    # your code
    ...


if __name__ == "__main__":
    assert max_depth(from_array([3, 9, 20, None, None, 15, 7])) == 3
    assert max_depth(from_array([1, None, 2])) == 2
    assert max_depth(from_array([])) == 0
    assert max_depth(from_array([1])) == 1
    print("all tests passed")
```

**Walk-through:**

```python
def max_depth(root):
    if root is None:
        return 0
    return 1 + max(max_depth(root.left), max_depth(root.right))
```

## Part D — *Maximum Depth* in Java 21

```java
public static int maxDepth(TreeNode root) {
    if (root == null) return 0;
    return 1 + Math.max(maxDepth(root.left), maxDepth(root.right));
}
```

## What you learned

- **Tree recursion.** Each call processes a node and recurses on children.
- **Base case.** `None`/`null` returns a sensible default (0 for depth,
  the same node for swaps, etc.).
- **Helper utilities.** `from_array` and `to_array` make tests readable.

➡️ **[challenge.md](./challenge.md)** then the [problems/](./problems/) in order.
