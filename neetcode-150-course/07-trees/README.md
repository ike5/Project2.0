# Module 07 — Trees 🌳

**Goal:** traverse and manipulate binary trees with confidence. ⏱️ ~8 h ·
🎯 Prereq: 06.

```
binary tree: O(h) descent, O(n) full traversal — recursion is the right tool
```

---

## 1. Why trees?

A **binary tree** is a hierarchical structure: each node has up to two
children (`left`, `right`). Trees model:

- Hierarchies (file systems, organization charts).
- Decision processes.
- Sorted data (BST — binary search tree).
- Recursive problems (most tree algorithms are naturally recursive).

The catch: recursion is the natural tool, and recursion can blow the stack
on a degenerate (linked-list-shaped) tree.

## 2. The four traversals

| Order | Visit | When |
|-------|-------|------|
| **Preorder** | node, left, right | Serialize a tree |
| **Inorder** | left, node, right | BST: yields sorted values |
| **Postorder** | left, right, node | Bottom-up computations (height, sum) |
| **Level-order** | level by level (BFS) | Right-side view, level sum |

## 3. The 15 problems — easy → hard

| #  | Problem | Difficulty | Technique |
|----|---------|-----------|-----------|
| 01 | [Invert Binary Tree](./problems/01-invert-binary-tree/) | Easy | Recursive swap |
| 02 | [Maximum Depth of Binary Tree](./problems/02-maximum-depth-of-binary-tree/) | Easy | Recursive depth |
| 03 | [Same Tree](./problems/03-same-tree/) | Easy | Recursive equality |
| 04 | [Subtree of Another Tree](./problems/04-subtree-of-another-tree/) | Easy | Walk + same-tree check |
| 05 | [Convert Sorted Array to BST](./problems/05-convert-sorted-array-to-binary-search-tree/) | Easy | Pick middle, recurse |
| 06 | [Kth Smallest Element in a BST](./problems/06-kth-smallest-element-in-a-bst/) | Medium | In-order, stop at k |
| 07 | [Validate Binary Search Tree](./problems/07-validate-binary-search-tree/) | Medium | Pass (lo, hi) range |
| 08 | [Lowest Common Ancestor of a BST](./problems/08-lowest-common-ancestor-of-a-binary-search-tree/) | Medium | Walk by range |
| 09 | [Construct from Preorder and Inorder](./problems/09-construct-binary-tree-from-preorder-and-inorder-traversal/) | Medium | Preorder root + inorder split |
| 10 | [Level Order Traversal](./problems/10-binary-tree-level-order-traversal/) | Medium | BFS, record level size |
| 11 | [Right Side View](./problems/11-binary-tree-right-side-view/) | Medium | BFS, take rightmost |
| 12 | [Count Good Nodes](./problems/12-count-good-nodes-in-binary-tree/) | Medium | DFS with max-so-far |
| 13 | [House Robber III](./problems/13-house-robber-iii/) | Medium | Return (rob, skip) |
| 14 | [Serialize and Deserialize](./problems/14-serialize-and-deserialize-binary-tree/) | Hard | Preorder DFS + nulls |
| 15 | [Maximum Path Sum](./problems/15-binary-tree-maximum-path-sum/) | Hard | Best through / single-branch |

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Class | `class TreeNode: val, left, right` | `static class TreeNode { int val; TreeNode left, right; }` |
| `None` vs `null` | `None` | `null` |
| Recursion limit | Default 1000 | Default large enough |
| Type checks | `isinstance(x, TreeNode)` | `x instanceof TreeNode` (Java 16+) / `x.getClass() == TreeNode.class` |
| Sort two int arrays | `sorted(a) == sorted(b)` | `Arrays.equals(a, b)` |
| Map<K,Integer> lookups | `d.get(k, 0)` | `d.getOrDefault(k, 0)` |

## 5. Common pitfalls

- **Validate BST by checking children only.** That misses deep violations.
  Always pass a `(lo, hi)` range down.
- **Building a tree from a list.** The catalog uses a level-order array with
  `None`/`null` for missing nodes. Be careful with trailing `None`s —
  `to_array` trims them, but `from_array` needs them to know when to stop.
- **Long.MAX_VALUE / MIN_VALUE in BST validation.** Use `long` in Java
  to avoid overflow when the values are near `Integer.MAX_VALUE`.
- **Cycle in serialization.** If your format can't represent the null
  children, you can't round-trip a tree.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then the [problems/](./problems/) in order.

## Key terms

inorder · preorder · postorder · level-order · height · depth · BST ·
valid BST · LCA · path sum · DFS · BFS

**Next →** [Module 08: Tries](../08-tries/)
