"""Module 07 — Trees problem catalog.

We use a minimal `TreeNode` class with `val`, `left`, `right`. For
deserialization, `None`/`null` is represented as a special sentinel.
"""

PROBLEMS = []


def add(slug, name, difficulty, brief, examples, constraints, hints,
        py_sig, py_body, py_tests, java_sig, java_body, java_tests,
        walkthrough):
    PROBLEMS.append({
        "slug": slug, "name": name, "difficulty": difficulty,
        "brief": brief, "examples": examples, "constraints": constraints,
        "hints": hints, "py_sig": py_sig, "py_body": py_body,
        "py_tests": py_tests, "java_sig": java_sig, "java_body": java_body,
        "java_tests": java_tests, "walkthrough": walkthrough,
    })


# 1. Invert Binary Tree (Easy)
add(
    "01-invert-binary-tree", "Invert Binary Tree", "Easy",
    "Given the `root` of a binary tree, invert the tree, and return its "
    "root.",
    [
        ("root = [4,2,7,1,3,6,9]", "[4,7,2,9,6,3,1]"),
        ("root = [2,1,3]", "[2,3,1]"),
    ],
    [
        "0 <= number of nodes <= 100",
        "-100 <= Node.val <= 100",
    ],
    [
        "Recursive: swap each node's left and right, recurse on both.",
    ],
    "def invert_tree(root: list[int | None]) -> list[int | None]:",
    """    # 'root' is a level-order array (nulls allowed)
    def from_array(arr: list[int | None]):
        if not arr or arr[0] is None:
            return None
        nodes = [None if v is None else TreeNode(v) for v in arr]
        kids = nodes[1:]
        for parent in nodes:
            if parent is None:
                continue
            left = kids.pop(0) if kids else None
            right = kids.pop(0) if kids else None
            parent.left = left
            parent.right = right
        return nodes[0]

    def to_array(node):
        if node is None:
            return []
        out: list[int | None] = []
        q = [node]
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

    t = from_array(root)
    def invert(node):
        if node is None:
            return None
        node.left, node.right = invert(node.right), invert(node.left)
        return node
    return to_array(invert(t))""",
    [
        (([4, 2, 7, 1, 3, 6, 9],), [4, 7, 2, 9, 6, 3, 1]),
        (([2, 1, 3],), [2, 3, 1]),
        (([],), []),
    ],
    "public static TreeNode invertTree(TreeNode root)",
    """        if (root == null) return null;
        TreeNode tmp = root.left;
        root.left = invertTree(root.right);
        root.right = invertTree(tmp);
        return root""",
    [],
    """Recursive swap. The base case is the empty tree.

**Time:** O(n). **Space:** O(h) for the recursion stack.
""",
)

# 2. Maximum Depth of Binary Tree (Easy)
add(
    "02-maximum-depth-of-binary-tree", "Maximum Depth of Binary Tree", "Easy",
    "Given the `root` of a binary tree, return its maximum depth. A binary "
    "tree's maximum depth is the number of nodes along the longest path "
    "from the root node down to the farthest leaf node.",
    [
        ("root = [3,9,20,null,null,15,7]", "3"),
        ("root = [1,null,2]", "2"),
    ],
    [
        "0 <= number of nodes <= 10^4",
        "-100 <= Node.val <= 100",
    ],
    [
        "Recursive: 1 + max(depth(left), depth(right)).",
        "Iterative: BFS, count levels.",
    ],
    "def max_depth(root: list[int | None]) -> int:",
    """    t = from_array(root)

    def depth(node):
        if node is None:
            return 0
        return 1 + max(depth(node.left), depth(node.right))

    return depth(t)""",
    [
        (([3, 9, 20, None, None, 15, 7],), 3),
        (([1, None, 2],), 2),
        (([],), 0),
        (([1],), 1),
    ],
    "public static int maxDepth(TreeNode root)",
    """        if (root == null) return 0;
        return 1 + Math.max(maxDepth(root.left), maxDepth(root.right))""",
    [],
    """Recursive: 1 + max of children's depths.

**Time:** O(n). **Space:** O(h) recursion.
""",
)

# 3. Same Tree (Easy)
add(
    "03-same-tree", "Same Tree", "Easy",
    "Given the roots of two binary trees `p` and `q`, write a function to "
    "check if they are the same or not. Two binary trees are considered "
    "the same if they are structurally identical, and the nodes have the "
    "same value.",
    [
        ("p = [1,2,3], q = [1,2,3]", "True"),
        ("p = [1,2], q = [1,null,2]", "False"),
    ],
    [
        "0 <= number of nodes <= 100",
        "-10^4 <= Node.val <= 10^4",
    ],
    [
        "Recursive: both null → true; one null → false; compare values and recurse on both children.",
    ],
    "def is_same_tree(p: list[int | None], q: list[int | None]) -> bool:",
    """    a = from_array(p)
    b = from_array(q)

    def same(x, y):
        if x is None and y is None:
            return True
        if x is None or y is None:
            return False
        return x.val == y.val and same(x.left, y.left) and same(x.right, y.right)

    return same(a, b)""",
    [
        (([1, 2, 3], [1, 2, 3]), True),
        (([1, 2], [1, None, 2]), False),
        (([], []), True),
    ],
    "public static boolean isSameTree(TreeNode p, TreeNode q)",
    """        if (p == null && q == null) return true;
        if (p == null || q == null) return false;
        if (p.val != q.val) return false;
        return isSameTree(p.left, q.left) && isSameTree(p.right, q.right)""",
    [],
    """Recursive equality on both subtrees.

**Time:** O(min(n, m)). **Space:** O(h).
""",
)

# 4. Subtree of Another Tree (Easy)
add(
    "04-subtree-of-another-tree", "Subtree of Another Tree", "Easy",
    "Given the roots of two binary trees `root` and `subRoot`, return "
    "`True` if there is a subtree of `root` with the same structure and "
    "node values of `subRoot` and `False` otherwise.",
    [
        ("root = [3,4,5,1,2], subRoot = [4,1,2]", "True"),
        ("root = [3,4,5,1,2,null,null,null,null,0], subRoot = [4,1,2]", "False"),
    ],
    [
        "0 <= number of nodes <= 2000",
        "-10^4 <= Node.val <= 10^4",
    ],
    [
        "For each node in `root`, check if the subtree rooted there equals "
        "`subRoot`.",
        "Faster with KMP / hash, but the O(n*m) version is fine for "
        "interviews.",
    ],
    "def is_subtree(root: list[int | None], sub: list[int | None]) -> bool:",
    """    a = from_array(root)
    b = from_array(sub)

    def same(x, y):
        if x is None and y is None: return True
        if x is None or y is None: return False
        return x.val == y.val and same(x.left, y.left) and same(x.right, y.right)

    def walk(node):
        if node is None: return False
        if same(node, b): return True
        return walk(node.left) or walk(node.right)

    return walk(a)""",
    [
        (([3, 4, 5, 1, 2], [4, 1, 2]), True),
        (([3, 4, 5, 1, 2, None, None, None, None, 0], [4, 1, 2]), False),
        (([1, 1], [1]), True),
    ],
    "public static boolean isSubtree(TreeNode root, TreeNode subRoot)",
    """        if (root == null) return false;
        if (sameTree(root, subRoot)) return true;
        return isSubtree(root.left, subRoot) || isSubtree(root.right, subRoot);
    }

    private static boolean sameTree(TreeNode a, TreeNode b) {
        if (a == null && b == null) return true;
        if (a == null || b == null) return false;
        if (a.val != b.val) return false;
        return sameTree(a.left, b.left) && sameTree(a.right, b.right)""",
    [],
    """Walk `root`; at each node, check if the subtree rooted there equals
`subRoot`. If so, return true. Otherwise recurse.

**Time:** O(n · m) in the worst case. **Space:** O(h).
""",
)

# 5. Convert Sorted Array to Binary Search Tree (Easy)
add(
    "05-convert-sorted-array-to-binary-search-tree",
    "Convert Sorted Array to Binary Search Tree", "Easy",
    "Given an integer array `nums` where the elements are sorted in "
    "**ascending** order, convert it to a height-balanced binary search "
    "tree. A height-balanced tree is one in which the depths of the two "
    "subtrees of every node never differ by more than 1.",
    [
        ("nums = [-10,-3,0,5,9]", "[0,-3,9,-10,null,5]"),
        ("nums = [1,3]", "[3,1]"),
    ],
    [
        "1 <= len(nums) <= 10^4",
        "-10^4 <= nums[i] <= 10^4",
        "nums is sorted in strictly increasing order",
    ],
    [
        "Recurse: pick the middle as root, recurse on left and right halves.",
    ],
    "def sorted_array_to_bst(nums: list[int]) -> list[int | None]:",
    """    def build(lo, hi):
        if lo > hi: return None
        mid = (lo + hi) // 2
        node = TreeNode(nums[mid])
        node.left = build(lo, mid - 1)
        node.right = build(mid + 1, hi)
        return node

    t = build(0, len(nums) - 1)
    return to_array(t)""",
    [
        (([-10, -3, 0, 5, 9],), [0, -10, 5, None, -3, None, 9]),
        (([1, 3],), [1, None, 3]),
    ],
    "public static TreeNode sortedArrayToBST(int[] nums)",
    """        return build(nums, 0, nums.length - 1);
    }

    private static TreeNode build(int[] nums, int lo, int hi) {
        if (lo > hi) return null;
        int mid = lo + (hi - lo) / 2;
        TreeNode node = new TreeNode(nums[mid]);
        node.left = build(nums, lo, mid - 1);
        node.right = build(nums, mid + 1, hi);
        return node;""",
    [],
    """Pick the middle as root, recurse on left and right halves. Picking
the *exact* middle keeps the tree balanced.

**Time:** O(n). **Space:** O(h) for the recursion; O(n) total nodes.
""",
)

# 6. Kth Smallest Element in a BST (Medium)
add(
    "06-kth-smallest-element-in-a-bst", "Kth Smallest Element in a BST",
    "Medium",
    "Given the `root` of a binary search tree, and an integer `k`, return "
    "the `k`th smallest value (1-indexed) of all the values of the nodes "
    "in the tree.",
    [
        ("root = [3,1,4,null,2], k = 1", "1"),
        ("root = [5,3,6,2,4,null,null,1], k = 3", "3"),
    ],
    [
        "1 <= k <= number of nodes <= 10^4",
        "0 <= Node.val <= 10^4",
    ],
    [
        "In-order traversal of a BST yields sorted values; stop at the kth.",
        "Or, augmented BST with subtree sizes for O(h) queries (not in "
        "this course).",
    ],
    "def kth_smallest(root: list[int | None], k: int) -> int:",
    """    t = from_array(root)
    stack: list = []
    cur = t
    while cur or stack:
        while cur:
            stack.append(cur)
            cur = cur.left
        cur = stack.pop()
        k -= 1
        if k == 0:
            return cur.val
        cur = cur.right
    return -1""",
    [
        (([3, 1, 4, None, 2], 1), 1),
        (([5, 3, 6, 2, 4, None, None, 1], 3), 3),
    ],
    "public static int kthSmallest(TreeNode root, int k)",
    """        Deque<TreeNode> stack = new ArrayDeque<>();
        TreeNode cur = root;
        while (cur != null || !stack.isEmpty()) {
            while (cur != null) {
                stack.push(cur);
                cur = cur.left;
            }
            cur = stack.pop();
            if (--k == 0) return cur.val;
            cur = cur.right;
        }
        return -1""",
    [],
    """Iterative in-order traversal. Stop when we've seen `k` nodes.

**Time:** O(h + k). **Space:** O(h).
""",
)

# 7. Validate Binary Search Tree (Medium)
add(
    "07-validate-binary-search-tree", "Validate Binary Search Tree", "Medium",
    "Given the `root` of a binary tree, determine if it is a valid binary "
    "search tree (BST). A valid BST is defined as follows: the left "
    "subtree of a node contains only nodes with keys **less than** the "
    "node's key; the right subtree of a node contains only nodes with keys "
    "**greater than** the node's key; both the left and right subtrees "
    "must also be binary search trees.",
    [
        ("root = [2,1,3]", "True"),
        ("root = [5,1,4,null,null,3,6]", "False"),
    ],
    [
        "1 <= number of nodes <= 10^4",
        "-2^31 <= Node.val <= 2^31 - 1",
    ],
    [
        "Don't just check `left.val < node.val < right.val` — that misses "
        "violations deeper in the tree.",
        "Pass a (lo, hi) range down. Each node must lie in its range.",
    ],
    "def is_valid_bst(root: list[int | None]) -> bool:",
    """    t = from_array(root)

    def valid(node, lo, hi):
        if node is None: return True
        if not (lo < node.val < hi): return False
        return valid(node.left, lo, node.val) and valid(node.right, node.val, hi)

    return valid(t, float('-inf'), float('inf'))""",
    [
        (([2, 1, 3],), True),
        (([5, 1, 4, None, None, 3, 6],), False),
        (([],), True),
    ],
    "public static boolean isValidBST(TreeNode root)",
    """        return valid(root, Long.MIN_VALUE, Long.MAX_VALUE);
    }

    private static boolean valid(TreeNode node, long lo, long hi) {
        if (node == null) return true;
        if (node.val <= lo || node.val >= hi) return false;
        return valid(node.left, lo, node.val) && valid(node.right, node.val, hi);""",
    [],
    """Pass a `(lo, hi)` range down. Each node's value must be in `(lo,
hi)`. Children inherit the parent's range narrowed by the parent's value.

> **Java note:** use `long` for `lo, hi` so `Integer.MIN_VALUE /
> Integer.MAX_VALUE` (the initial range) work correctly.
""",
)

# 8. Lowest Common Ancestor of a BST (Medium)
add(
    "08-lowest-common-ancestor-of-a-binary-search-tree",
    "Lowest Common Ancestor of a Binary Search Tree", "Medium",
    "Given a binary search tree (BST), find the lowest common ancestor "
    "(LCA) of two given nodes in the BST. The LCA is the lowest node in "
    "T that has both p and q as descendants (a node can be a descendant "
    "of itself).",
    [
        ("root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8", "6"),
        ("root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4", "2"),
    ],
    [
        "2 <= number of nodes <= 10^5",
        "-10^9 <= Node.val <= 10^9",
        "All Node.val are unique",
        "p != q",
        "p and q exist in the BST",
    ],
    [
        "Walk from the root. If both p and q are smaller, go left; if both "
        "larger, go right; otherwise, current is the LCA.",
    ],
    "def lowest_common_ancestor_bst(root: list[int | None], p: int, q: int) -> int:",
    """    t = from_array(root)
    cur = t
    while cur:
        if p < cur.val and q < cur.val:
            cur = cur.left
        elif p > cur.val and q > cur.val:
            cur = cur.right
        else:
            return cur.val
    return -1""",
    [
        (([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 8), 6),
        (([6, 2, 8, 0, 4, 7, 9, None, None, 3, 5], 2, 4), 2),
    ],
    "public static int lowestCommonAncestorBST(TreeNode root, int p, int q)",
    """        TreeNode cur = root;
        while (cur != null) {
            if (p < cur.val && q < cur.val) cur = cur.left;
            else if (p > cur.val && q > cur.val) cur = cur.right;
            else return cur.val;
        }
        return -1;""",
    [],
    """Because it's a BST, the LCA is the first node whose value is
**between** p and q. Walk from the root, branching left or right until
the current node splits them.

**Time:** O(h). **Space:** O(1).
""",
)

# 9. Construct Binary Tree from Preorder and Inorder Traversal (Medium)
add(
    "09-construct-binary-tree-from-preorder-and-inorder-traversal",
    "Construct Binary Tree from Preorder and Inorder Traversal", "Medium",
    "Given two integer arrays `preorder` and `inorder` where `preorder` is "
    "the preorder traversal of a binary tree and `inorder` is the inorder "
    "traversal of the same tree, construct and return the binary tree.",
    [
        ("preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]",
         "[3,9,20,null,null,15,7]"),
    ],
    [
        "1 <= len(preorder) == len(inorder) <= 3000",
        "-3000 <= preorder[i], inorder[i] <= 3000",
        "All values are unique",
    ],
    [
        "Preorder's first element is the root. In inorder, the root splits "
        "left and right subtrees.",
        "Recurse on the two halves. Use a hash map for O(1) lookups in "
        "inorder.",
    ],
    "def build_tree(preorder: list[int], inorder: list[int]) -> list[int | None]:",
    """    idx = {v: i for i, v in enumerate(inorder)}
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
    return to_array(t)""",
    [
        (([3, 9, 20, 15, 7], [9, 3, 15, 20, 7]), [3, 9, 20, None, None, 15, 7]),
    ],
    "public static TreeNode buildTree(int[] preorder, int[] inorder)",
    """        Map<Integer, Integer> idx = new HashMap<>();
        for (int i = 0; i < inorder.length; i++) idx.put(inorder[i], i);
        return build(preorder, idx, new int[]{0}, 0, inorder.length - 1);
    }

    private static TreeNode build(int[] preorder, Map<Integer, Integer> idx, int[] pi, int lo, int hi) {
        if (lo > hi) return null;
        TreeNode root = new TreeNode(preorder[pi[0]++]);
        int mid = idx.get(root.val);
        root.left = build(preorder, idx, pi, lo, mid - 1);
        root.right = build(preorder, idx, pi, mid + 1, hi);
        return root;""",
    [],
    """Preorder gives us the root (first element). In inorder, the root
splits the array into left and right subtree elements. Recurse on each
half.

A `dict[value, index]` over inorder gives O(1) lookups, making the
overall algorithm O(n).

**Time:** O(n). **Space:** O(n) for the map and recursion.
""",
)

# 10. Binary Tree Level Order Traversal (Medium)
add(
    "10-binary-tree-level-order-traversal", "Binary Tree Level Order Traversal",
    "Medium",
    "Given the `root` of a binary tree, return the level order traversal "
    "of its nodes' values (i.e., from left to right, level by level).",
    [
        ("root = [3,9,20,null,null,15,7]", "[[3],[9,20],[15,7]]"),
        ("root = [1]", "[[1]]"),
    ],
    [
        "0 <= number of nodes <= 2000",
        "-1000 <= Node.val <= 1000",
    ],
    [
        "BFS with a queue. Record the size at the start of each level.",
    ],
    "def level_order(root: list[int | None]) -> list[list[int]]:",
    """    t = from_array(root)
    if t is None: return []
    out: list[list[int]] = []
    q = [t]
    while q:
        level: list[int] = []
        for _ in range(len(q)):
            n = q.pop(0)
            level.append(n.val)
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
        out.append(level)
    return out""",
    [
        (([3, 9, 20, None, None, 15, 7],), [[3], [9, 20], [15, 7]]),
        (([1],), [[1]]),
    ],
    "public static List<List<Integer>> levelOrder(TreeNode root)",
    """        List<List<Integer>> out = new ArrayList<>();
        if (root == null) return out;
        Deque<TreeNode> q = new ArrayDeque<>();
        q.offer(root);
        while (!q.isEmpty()) {
            int size = q.size();
            List<Integer> level = new ArrayList<>();
            for (int i = 0; i < size; i++) {
                TreeNode n = q.poll();
                level.add(n.val);
                if (n.left != null) q.offer(n.left);
                if (n.right != null) q.offer(n.right);
            }
            out.add(level);
        }
        return out""",
    [],
    """BFS. At each iteration, the queue contains *exactly* one level;
record its size, then drain it.

**Time:** O(n). **Space:** O(w) where w is the maximum level width.
""",
)

# 11. Binary Tree Right Side View (Medium)
add(
    "11-binary-tree-right-side-view", "Binary Tree Right Side View", "Medium",
    "Given the `root` of a binary tree, imagine yourself standing on the "
    "right side of it, return the values of the nodes you can see ordered "
    "from top to bottom.",
    [
        ("root = [1,2,3,null,5,null,4]", "[1,3,4]"),
        ("root = [1,null,3]", "[1,3]"),
    ],
    [
        "0 <= number of nodes <= 100",
        "-100 <= Node.val <= 100",
    ],
    [
        "BFS: take the last element of each level.",
        "Or: DFS, going right first; record each new depth's first node.",
    ],
    "def right_side_view(root: list[int | None]) -> list[int]:",
    """    t = from_array(root)
    if t is None: return []
    out: list[int] = []
    q = [t]
    while q:
        for i in range(len(q)):
            n = q.pop(0)
            if i == len(q):  # after pop, original-size - 1 - i was 0
                pass
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
        # wrong logic above; redo: record rightmost BEFORE popping children
    # corrected version:
    out = []
    q = [t]
    while q:
        sz = len(q)
        for i in range(sz):
            n = q.pop(0)
            if i == sz - 1:
                out.append(n.val)
            if n.left: q.append(n.left)
            if n.right: q.append(n.right)
    return out""",
    [
        (([1, 2, 3, None, 5, None, 4],), [1, 3, 4]),
        (([1, None, 3],), [1, 3]),
    ],
    "public static List<Integer> rightSideView(TreeNode root)",
    """        List<Integer> out = new ArrayList<>();
        if (root == null) return out;
        Deque<TreeNode> q = new ArrayDeque<>();
        q.offer(root);
        while (!q.isEmpty()) {
            int size = q.size();
            for (int i = 0; i < size; i++) {
                TreeNode n = q.poll();
                if (i == size - 1) out.add(n.val);
                if (n.left != null) q.offer(n.left);
                if (n.right != null) q.offer(n.right);
            }
        }
        return out""",
    [],
    """BFS: at each level, the last node is the rightmost. Record it.

**Time:** O(n). **Space:** O(w).
""",
)

# 12. Count Good Nodes in Binary Tree (Medium)
add(
    "12-count-good-nodes-in-binary-tree", "Count Good Nodes in Binary Tree",
    "Medium",
    "Given a binary tree `root`, a node `x` in the tree is named **good** "
    "if in the path from root to `x`, there are no nodes with a value "
    "greater than `x`'s. Return the number of good nodes in the binary "
    "tree.",
    [
        ("root = [3,1,4,3,null,1,5]", "4"),
        ("root = [3,3,null,4,2]", "3"),
    ],
    [
        "1 <= number of nodes <= 10^5",
        "-10^4 <= Node.val <= 10^4",
    ],
    [
        "DFS: pass the max so far down. A node is good if its val >= max.",
    ],
    "def good_nodes(root: list[int | None]) -> int:",
    """    t = from_array(root)

    def dfs(node, max_so_far):
        if node is None: return 0
        good = 1 if node.val >= max_so_far else 0
        new_max = max(max_so_far, node.val)
        return good + dfs(node.left, new_max) + dfs(node.right, new_max)

    return dfs(t, float('-inf'))""",
    [
        (([3, 1, 4, 3, None, 1, 5],), 4),
        (([3, 3, None, 4, 2],), 3),
    ],
    "public static int goodNodes(TreeNode root)",
    """        return dfs(root, Integer.MIN_VALUE);
    }

    private static int dfs(TreeNode node, int maxSoFar) {
        if (node == null) return 0;
        int good = (node.val >= maxSoFar) ? 1 : 0;
        int newMax = Math.max(maxSoFar, node.val);
        return good + dfs(node.left, newMax) + dfs(node.right, newMax);""",
    [],
    """DFS with a `max_so_far` parameter. The root is always good.

**Time:** O(n). **Space:** O(h).
""",
)

# 13. House Robber III (Medium)
add(
    "13-house-robber-iii", "House Robber III", "Medium",
    "The thief has found himself a new place for his thievery again. "
    "There is only one entrance to this area, called `root`. Besides the "
    "`root`, each house has one and only one parent house. After a tour, "
    "the smart thief realized that all houses in this place form a binary "
    "tree. It will automatically contact the police if two directly-linked "
    "houses were broken into on the same night. Determine the maximum "
    "amount of money the thief can rob tonight without alerting the "
    "police.",
    [
        ("root = [3,2,3,null,3,null,1]", "7"),
        ("root = [3,4,5,1,3,null,1]", "9"),
    ],
    [
        "0 <= number of nodes <= 10^4",
        "0 <= Node.val <= 10^4",
    ],
    [
        "For each node, return `(rob, skip)` — the best if we rob or skip "
        "this node.",
        "If we rob, we add val + skip(left) + skip(right). If we skip, we "
        "take max(rob or skip) of each child.",
    ],
    "def rob_tree(root: list[int | None]) -> int:",
    """    t = from_array(root)

    def dfs(node):
        if node is None: return (0, 0)
        lr, ls = dfs(node.left)
        rr, rs = dfs(node.right)
        rob = node.val + ls + rs
        skip = max(lr, ls) + max(rr, rs)
        return (rob, skip)

    return max(dfs(t))""",
    [
        (([3, 2, 3, None, 3, None, 1],), 7),
        (([3, 4, 5, 1, 3, None, 1],), 9),
    ],
    "public static int robTree(TreeNode root)",
    """        int[] res = dfs(root);
        return Math.max(res[0], res[1]);
    }

    private static int[] dfs(TreeNode node) {
        if (node == null) return new int[]{0, 0};
        int[] l = dfs(node.left);
        int[] r = dfs(node.right);
        int rob = node.val + l[1] + r[1];
        int skip = Math.max(l[0], l[1]) + Math.max(r[0], r[1]);
        return new int[]{rob, skip};""",
    [],
    """Each subtree returns `(rob, skip)`. Combining:
- `rob = val + skip(left) + skip(right)`
- `skip = max(rob, skip)(left) + max(rob, skip)(right)`

**Time:** O(n). **Space:** O(h).
""",
)

# 14. Serialize and Deserialize Binary Tree (Hard)
add(
    "14-serialize-and-deserialize-binary-tree",
    "Serialize and Deserialize Binary Tree", "Hard",
    "Serialization is the process of converting a data structure or "
    "object into a sequence of bits so that it can be stored in a file or "
    "memory buffer, or transmitted across a network connection link to be "
    "reconstructed later in the same or another computer environment. "
    "Design an algorithm to serialize and deserialize a binary tree.",
    [
        ("root = [1,2,3,null,null,4,5]", "1,2,None,None,3,4,None,None,5,None,None"),
    ],
    [
        "0 <= number of nodes <= 10^4",
        "-1000 <= Node.val <= 1000",
    ],
    [
        "Preorder DFS. Serialize: 'val,null,null,...' for missing "
        "children.",
        "Deserialize: read tokens; null consumes nothing, value creates a "
        "node and recurses on left and right.",
    ],
    "def serialize(root: list[int | None]) -> str:",
    """    t = from_array(root)
    out: list[str] = []

    def dfs(node):
        if node is None:
            out.append('null')
            return
        out.append(str(node.val))
        dfs(node.left)
        dfs(node.right)

    dfs(t)
    return ','.join(out)""",
    [
        (([1, 2, 3, None, None, 4, 5],), "1,2,null,null,3,4,null,null,5,null,null"),
    ],
    "public static String serialize(TreeNode root)",
    """        StringBuilder sb = new StringBuilder();
        dfs(root, sb);
        return sb.toString();
    }

    private static void dfs(TreeNode node, StringBuilder sb) {
        if (node == null) { sb.append("null,"); return; }
        sb.append(node.val).append(',');
        dfs(node.left, sb);
        dfs(node.right, sb);""",
    [],
    """**Preorder DFS** is the simplest format. Serialize writes `val` or
`null` for each visit. Deserialize uses a queue of tokens.

**Time:** O(n). **Space:** O(n).
""",
)

# 15. Binary Tree Maximum Path Sum (Hard)
add(
    "15-binary-tree-maximum-path-sum", "Binary Tree Maximum Path Sum",
    "Hard",
    "A **path** in a binary tree is a sequence of nodes where each pair of "
    "adjacent nodes in the sequence has an edge connecting them. A node "
    "can only appear in the sequence at most once. Note that the path "
    "does not need to pass through the root. The **path sum** of a path "
    "is the sum of the node's values in the path. Given the `root` of a "
    "binary tree, return the maximum path sum of any **non-empty** path.",
    [
        ("root = [1,2,3]", "6"),
        ("root = [-10,9,20,null,null,15,7]", "42"),
    ],
    [
        "1 <= number of nodes <= 3 * 10^4",
        "-1000 <= Node.val <= 1000",
    ],
    [
        "For each node, compute the best 'path through this node'. Update "
        "global max.",
        "Return the best 'single-branch' path going up (so the parent can "
        "use us as a side).",
    ],
    "def max_path_sum(root: list[int | None]) -> int:",
    """    t = from_array(root)
    best = [float('-inf')]

    def gain(node):
        if node is None: return 0
        left = max(0, gain(node.left))
        right = max(0, gain(node.right))
        best[0] = max(best[0], node.val + left + right)
        return node.val + max(left, right)

    gain(t)
    return best[0]""",
    [
        (([1, 2, 3],), 6),
        (([-10, 9, 20, None, None, 15, 7],), 42),
        (([-3],), -3),
    ],
    "public static int maxPathSum(TreeNode root)",
    """        int[] best = { Integer.MIN_VALUE };
        gain(root, best);
        return best[0];
    }

    private static int gain(TreeNode node, int[] best) {
        if (node == null) return 0;
        int left = Math.max(0, gain(node.left, best));
        int right = Math.max(0, gain(node.right, best));
        best[0] = Math.max(best[0], node.val + left + right);
        return node.val + Math.max(left, right);""",
    [],
    """For each node, the best path **through it** is
`node.val + max(0, left_gain) + max(0, right_gain)`. The best
**single-branch** path going up is `node.val + max(0, max(left_gain,
right_gain))`.

**Time:** O(n). **Space:** O(h).
""",
)
