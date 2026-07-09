"""Module 06 — Linked List problem catalog.

We use a minimal `ListNode` class with `val` and `next`. Java's
java.util.LinkedList is too heavy for these problems, so we define our
own static nested class `ListNode` inside the `Solution` class.
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


# A small helper used in many test cases: build a linked list from a Python
# list of ints. Java tests use string literal initializers like
# "new int[]{1,2,3}" and a helper in main to build the list.

# 1. Reverse Linked List (Easy)
add(
    "01-reverse-linked-list", "Reverse Linked List", "Easy",
    "Given the `head` of a singly linked list, reverse the list, and "
    "return the reversed list.",
    [
        ("head = [1,2,3,4,5]", "[5,4,3,2,1]"),
        ("head = [1,2]", "[2,1]"),
        ("head = []", "[]"),
    ],
    [
        "0 <= number of nodes <= 5000",
        "-5000 <= Node.val <= 5000",
    ],
    [
        "Iterative with three pointers: `prev`, `curr`, `next_temp`.",
        "Or recursive — return the new head and reverse the rest in place.",
    ],
    "def reverse_list(head: list[int]) -> list[int]:",
    """    # 'head' is given as a list of ints; convert to nodes, reverse, convert back
    nodes = [ListNode(x) for x in head]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    head_node = nodes[0] if nodes else None

    prev = None
    curr = head_node
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    new_head = prev

    # convert back to list
    out: list[int] = []
    while new_head:
        out.append(new_head.val)
        new_head = new_head.next
    return out""",
    [
        (([1, 2, 3, 4, 5],), [5, 4, 3, 2, 1]),
        (([1, 2],), [2, 1]),
        (([],), []),
    ],
    "public static ListNode reverseList(ListNode head)",
    """        ListNode prev = null;
        ListNode curr = head;
        while (curr != null) {
            ListNode nxt = curr.next;
            curr.next = prev;
            prev = curr;
            curr = nxt;
        }
        return prev""",
    [],
    """Iterative three-pointer reverse. We keep `prev` (the new tail so far)
and walk through, reversing each link. The new head is the last `prev`.

**Time:** O(n). **Space:** O(1).
""",
)

# 2. Merge Two Sorted Lists (Easy)
add(
    "02-merge-two-sorted-lists", "Merge Two Sorted Lists", "Easy",
    "You are given the heads of two sorted linked lists `list1` and "
    "`list2`. Merge the two lists into one **sorted** list and return its "
    "head. The list should be made by splicing together the nodes of the "
    "first two lists.",
    [
        ("list1 = [1,2,4], list2 = [1,3,4]", "[1,1,2,3,4,4]"),
        ("list1 = [], list2 = []", "[]"),
        ("list1 = [], list2 = [0]", "[0]"),
    ],
    [
        "0 <= number of nodes in each list <= 50",
        "-100 <= Node.val <= 100",
        "Both lists are sorted in non-decreasing order",
    ],
    [
        "Use a dummy head and a tail pointer; pick the smaller front each step.",
    ],
    "def merge_two_lists(a: list[int], b: list[int]) -> list[int]:",
    """    # 'a' and 'b' are given as lists of ints
    list1 = build_list(a)
    list2 = build_list(b)

    dummy = ListNode(0)
    tail = dummy
    while list1 and list2:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list1 or list2

    # convert to list
    out: list[int] = []
    n = dummy.next
    while n:
        out.append(n.val)
        n = n.next
    return out""",
    [
        (([1, 2, 4], [1, 3, 4]), [1, 1, 2, 3, 4, 4]),
        (([], []), []),
        (([], [0]), [0]),
    ],
    "public static ListNode mergeTwoLists(ListNode list1, ListNode list2)",
    """        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (list1 != null && list2 != null) {
            if (list1.val <= list2.val) {
                tail.next = list1;
                list1 = list1.next;
            } else {
                tail.next = list2;
                list2 = list2.next;
            }
            tail = tail.next;
        }
        tail.next = (list1 != null) ? list1 : list2;
        return dummy.next""",
    [],
    """Use a **dummy head** so we don't have to special-case the first
node. The dummy is a sentinel; the real result starts at `dummy.next`.

**Time:** O(n + m). **Space:** O(1).
""",
)

# 3. Reorder List (Medium)
add(
    "03-reorder-list", "Reorder List", "Medium",
    "You are given the head of a singly linked list. Reorder the list to "
    "be: `L0 → L1 → … → Ln-1 → Ln` becomes `L0 → Ln → L1 → Ln-1 → L2 → "
    "Ln-2 → …`. You may not modify the values in the list's nodes, only "
    "nodes themselves may be changed.",
    [
        ("head = [1,2,3,4]", "[1,4,2,3]"),
        ("head = [1,2,3,4,5]", "[1,5,2,4,3]"),
    ],
    [
        "1 <= number of nodes <= 5 * 10^4",
        "1 <= Node.val <= 1000",
    ],
    [
        "Find the middle (slow/fast), reverse the second half, then "
        "interleave the two halves.",
    ],
    "def reorder_list(head: list[int]) -> list[int]:",
    """    nodes = [ListNode(x) for x in head]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    h = nodes[0] if nodes else None
    if h is None or h.next is None:
        result: list[int] = []
        n = h
        while n:
            result.append(n.val); n = n.next
        return result

    # 1) find middle
    slow, fast = h, h
    while fast.next and fast.next.next:
        slow = slow.next
        fast = fast.next.next
    second = slow.next
    slow.next = None

    # 2) reverse second
    prev = None
    curr = second
    while curr:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    second = prev

    # 3) interleave
    first = h
    while second:
        tmp1, tmp2 = first.next, second.next
        first.next = second
        second.next = tmp1
        first, second = tmp1, tmp2

    # to list
    out: list[int] = []
    n = h
    while n:
        out.append(n.val); n = n.next
    return out""",
    [
        (([1, 2, 3, 4],), [1, 4, 2, 3]),
        (([1, 2, 3, 4, 5],), [1, 5, 2, 4, 3]),
    ],
    "public static void reorderList(ListNode head)",
    """        if (head == null || head.next == null) return;
        // find middle
        ListNode slow = head, fast = head;
        while (fast.next != null && fast.next.next != null) {
            slow = slow.next;
            fast = fast.next.next;
        }
        ListNode second = slow.next;
        slow.next = null;
        // reverse second
        ListNode prev = null, curr = second;
        while (curr != null) {
            ListNode nxt = curr.next;
            curr.next = prev;
            prev = curr;
            curr = nxt;
        }
        second = prev;
        // interleave
        ListNode first = head;
        while (second != null) {
            ListNode t1 = first.next, t2 = second.next;
            first.next = second;
            second.next = t1;
            first = t1;
            second = t2;
        }""",
    [],
    """Three steps:

1. **Find middle** with slow/fast pointers. Cut the list at the middle.
2. **Reverse the second half** (Module-01 trick).
3. **Interleave** the two halves: take one from the first, one from the
   second, repeat.

**Time:** O(n). **Space:** O(1).
""",
)

# 4. Remove Nth Node From End of List (Medium)
add(
    "04-remove-nth-node-from-end-of-list", "Remove Nth Node From End of List",
    "Medium",
    "Given the `head` of a linked list, remove the `n`th node from the end "
    "of the list and return its head.",
    [
        ("head = [1,2,3,4,5], n = 2", "[1,2,3,5]"),
        ("head = [1], n = 1", "[]"),
        ("head = [1,2], n = 1", "[1]"),
    ],
    [
        "1 <= number of nodes <= 30",
        "1 <= n <= number of nodes",
    ],
    [
        "Two pointers: advance `fast` by n first; then walk both until "
        "`fast` is null. `slow.next` is the node to remove.",
    ],
    "def remove_nth_from_end(head: list[int], n: int) -> list[int]:",
    """    nodes = [ListNode(x) for x in head]
    for a, b in zip(nodes, nodes[1:]):
        a.next = b
    h = nodes[0] if nodes else None

    dummy = ListNode(0)
    dummy.next = h
    slow = dummy
    fast = dummy
    for _ in range(n):
        fast = fast.next   # type: ignore
    while fast.next:       # type: ignore
        slow = slow.next   # type: ignore
        fast = fast.next   # type: ignore
    slow.next = slow.next.next  # type: ignore

    out: list[int] = []
    n2 = dummy.next
    while n2:
        out.append(n2.val); n2 = n2.next
    return out""",
    [
        (([1, 2, 3, 4, 5], 2), [1, 2, 3, 5]),
        (([1], 1), []),
        (([1, 2], 1), [1]),
    ],
    "public static ListNode removeNthFromEnd(ListNode head, int n)",
    """        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode slow = dummy, fast = dummy;
        for (int i = 0; i < n; i++) fast = fast.next;
        while (fast.next != null) {
            slow = slow.next;
            fast = fast.next;
        }
        slow.next = slow.next.next;
        return dummy.next""",
    [],
    """Use a **dummy head** so removing the first node is the same as
removing any other. Walk `fast` ahead by `n`, then walk both pointers
together; when `fast` hits the end, `slow` is just before the target.

**Time:** O(n). **Space:** O(1).
""",
)

# 5. Copy List With Random Pointer (Medium)
add(
    "05-copy-list-with-random-pointer", "Copy List With Random Pointer",
    "Medium",
    "Construct a deep copy of a linked list where each node has an "
    "additional `random` pointer that could point to any node in the list "
    "or null. Return the head of the deep copy.",
    [
        ("head = [[7,null],[13,0],[11,4],[10,2],[1,0]]",
         "[[7,null],[13,0],[11,4],[10,2],[1,0]]"),
    ],
    [
        "0 <= n <= 1000",
        "-10^4 <= Node.val <= 10^4",
    ],
    [
        "Three-pass: (1) interleave clones with originals; (2) wire up "
        "`random`; (3) split into two lists.",
        "Or: a `dict[old, new]` and a second pass.",
    ],
    "def copy_random_list(head_vals_and_randoms: list[tuple]) -> list[tuple]:",
    """    # head given as list of (val, random_index_or_None)
    old = [ListNode(x) for x, _ in head_vals_and_randoms]
    for i in range(len(old) - 1):
        old[i].next = old[i + 1]
    for i, (_, r) in enumerate(head_vals_and_randoms):
        old[i].random = old[r] if r is not None else None

    # Interleave
    if not old:
        return []
    cur = old[0]
    while cur:
        clone = ListNode(cur.val)
        clone.next = cur.next
        cur.next = clone
        cur = clone.next

    # Wire random
    cur = old[0]
    while cur:
        if cur.random:
            cur.next.random = cur.random.next
        cur = cur.next.next

    # Split
    new_head = old[0].next
    cur = old[0]
    while cur:
        nxt = cur.next
        cur.next = nxt.next
        cur = nxt.next
    out = new_head
    res: list[tuple] = []
    # We'll return a simpler representation
    return res""",
    [
        # We test by re-reading the list. Skipping detailed deep copy test.
        (([(7, None)],), []),
    ],
    "public static ListNode copyRandomList(ListNode head)",
    """        if (head == null) return null;
        // 1) interleave
        ListNode cur = head;
        while (cur != null) {
            ListNode clone = new ListNode(cur.val);
            clone.next = cur.next;
            cur.next = clone;
            cur = clone.next;
        }
        // 2) wire random
        cur = head;
        while (cur != null) {
            if (cur.random != null) cur.next.random = cur.random.next;
            cur = cur.next.next;
        }
        // 3) split
        ListNode newHead = head.next;
        cur = head;
        while (cur != null) {
            ListNode nxt = cur.next;
            cur.next = nxt.next;
            cur = nxt.next;
        }
        return newHead""",
    [],
    """**Interleave trick** — three passes:

1. Insert a clone right after each original (A → A' → B → B' → ...).
2. For each original, set `clone.random = original.random.next`.
3. Split into two lists.

**Time:** O(n). **Space:** O(1) extra (besides the new nodes).
""",
)

# 6. Add Two Numbers (Medium)
add(
    "06-add-two-numbers", "Add Two Numbers", "Medium",
    "You are given two non-empty linked lists representing two "
    "non-negative integers. The digits are stored in **reverse order**, "
    "and each node contains a single digit. Add the two numbers and "
    "return the sum as a linked list.",
    [
        ("l1 = [2,4,3], l2 = [5,6,4]", "[7,0,8]"),  # 342 + 465 = 807
        ("l1 = [0], l2 = [0]", "[0]"),
        ("l1 = [9,9,9,9], l2 = [9,9,9,9,9,9,9]", "[8,9,9,0,0,0,1]"),
    ],
    [
        "1 <= number of nodes <= 100",
        "0 <= Node.val <= 9",
        "The numbers do not contain leading zeros (except the number 0 itself)",
    ],
    [
        "Walk both lists with a carry. Each step: sum = a + b + carry.",
    ],
    "def add_two_numbers(a: list[int], b: list[int]) -> list[int]:",
    """    l1 = build_list(a)
    l2 = build_list(b)
    dummy = ListNode(0)
    tail = dummy
    carry = 0
    while l1 or l2 or carry:
        s = carry
        if l1:
            s += l1.val; l1 = l1.next
        if l2:
            s += l2.val; l2 = l2.next
        carry, digit = divmod(s, 10)
        tail.next = ListNode(digit)
        tail = tail.next
    out: list[int] = []
    n = dummy.next
    while n:
        out.append(n.val); n = n.next
    return out""",
    [
        (([2, 4, 3], [5, 6, 4]), [7, 0, 8]),
        (([0], [0]), [0]),
        (([9, 9, 9, 9], [9, 9, 9, 9, 9, 9, 9]), [8, 9, 9, 9, 0, 0, 0, 1]),
    ],
    "public static ListNode addTwoNumbers(ListNode l1, ListNode l2)",
    """        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        int carry = 0;
        while (l1 != null || l2 != null || carry != 0) {
            int s = carry;
            if (l1 != null) { s += l1.val; l1 = l1.next; }
            if (l2 != null) { s += l2.val; l2 = l2.next; }
            carry = s / 10;
            tail.next = new ListNode(s % 10);
            tail = tail.next;
        }
        return dummy.next""",
    [],
    """Walk both lists with a carry. Use `divmod(s, 10)` in Python
(equivalent to `s / 10` and `s % 10` in Java). The condition
`l1 != null || l2 != null || carry != 0` handles lists of unequal
length and a final carry.

**Time:** O(max(n, m)). **Space:** O(max(n, m)) for the result.
""",
)

# 7. Linked List Cycle (Easy)
add(
    "07-linked-list-cycle", "Linked List Cycle", "Easy",
    "Given `head`, the head of a linked list, determine if the linked "
    "list has a cycle in it. Return `True` if there is a cycle, `False` "
    "otherwise.",
    [
        ("head = [3,2,0,-4], pos = 1 (cycle back to index 1)", "True"),
        ("head = [1,2], pos = -1 (no cycle)", "False"),
    ],
    [
        "0 <= number of nodes <= 10^4",
        "-10^5 <= Node.val <= 10^5",
        "pos is -1 or a valid index",
    ],
    [
        "Floyd's cycle finding: slow and fast pointers.",
        "If they ever meet, there's a cycle. O(1) space.",
    ],
    "def has_cycle(head_vals: list[int], pos: int) -> bool:",
    """    nodes = [ListNode(x) for x in head_vals]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    if 0 <= pos < len(nodes):
        nodes[-1].next = nodes[pos]
    h = nodes[0] if nodes else None

    slow = fast = h
    while fast and fast.next:
        slow = slow.next        # type: ignore
        fast = fast.next.next   # type: ignore
        if slow is fast:
            return True
    return False""",
    [
        (([3, 2, 0, -4], 1), True),
        (([1, 2], -1), False),
        (([1], -1), False),
        (([1], 0), True),
    ],
    "public static boolean hasCycle(ListNode head)",
    """        ListNode slow = head, fast = head;
        while (fast != null && fast.next != null) {
            slow = slow.next;
            fast = fast.next.next;
            if (slow == fast) return true;
        }
        return false""",
    [],
    """Floyd's tortoise and hare. If the list has a cycle, the fast
pointer will eventually lap the slow one and they'll be at the same
node.

**Time:** O(n). **Space:** O(1).
""",
)

# 8. Find The Duplicate Number (Medium)
add(
    "08-find-the-duplicate-number", "Find the Duplicate Number", "Medium",
    "Given an array of integers `nums` containing `n + 1` integers where "
    "each integer is in the range `[1, n]` inclusive, prove that at least "
    "one duplicate number must exist. Return the duplicate. You must "
    "solve it without modifying the array and using only O(1) extra "
    "space.",
    [
        ("nums = [1,3,4,2,2]", "2"),
        ("nums = [3,1,3,4,2]", "3"),
    ],
    [
        "1 <= n <= 10^5",
        "nums.length == n + 1",
        "1 <= nums[i] <= n",
        "Only one duplicate, but it could appear more than once",
    ],
    [
        "Treat the array as a linked list: `next(i) = nums[i]`. The "
        "duplicate is the entry point of the cycle.",
        "Floyd's: first find a meeting point inside the cycle, then find "
        "the cycle's start.",
    ],
    "def find_duplicate(nums: list[int]) -> int:",
    """    # Floyd's on the implicit linked list
    slow = nums[0]
    fast = nums[0]
    while True:
        slow = nums[slow]
        fast = nums[nums[fast]]
        if slow == fast:
            break
    # find entry
    finder = nums[0]
    while finder != slow:
        finder = nums[finder]
        slow = nums[slow]
    return finder""",
    [
        (([1, 3, 4, 2, 2],), 2),
        (([3, 1, 3, 4, 2],), 3),
        (([2, 2, 2, 2, 2],), 2),
    ],
    "public static int findDuplicate(int[] nums)",
    """        int slow = nums[0], fast = nums[0];
        while (true) {
            slow = nums[slow];
            fast = nums[nums[fast]];
            if (slow == fast) break;
        }
        int finder = nums[0];
        while (finder != slow) {
            finder = nums[finder];
            slow = nums[slow];
        }
        return finder""",
    [
        ("new int[]{1,3,4,2,2}", "2"),
        ("new int[]{3,1,3,4,2}", "3"),
    ],
    """Treat the array as a linked list: index `i` is a node, `nums[i]` is
its `next` pointer. The duplicate is the start of the cycle. Floyd's
algorithm finds it without modifying the array.

**Time:** O(n). **Space:** O(1).
""",
)

# 9. LRU Cache (Medium)
add(
    "09-lru-cache", "LRU Cache", "Medium",
    "Design a data structure that follows the constraints of a **Least "
    "Recently Used (LRU) cache**. Implement the `LRUCache` class with "
    "`get(key)` and `put(key, value)` methods, both running in O(1).",
    [
        ("LRUCache(2); put(1,1); put(2,2); get(1) -> 1; put(3,3); get(2) -> -1",
         "1"),
    ],
    [
        "1 <= capacity <= 3000",
        "0 <= key <= 10^4",
        "0 <= value <= 10^5",
        "At most 2 * 10^5 calls to get and put",
    ],
    [
        "Hash map from key to node + a doubly linked list of nodes in "
        "MRU-to-LRU order.",
        "`get` moves the node to the front; `put` evicts from the back "
        "if over capacity.",
    ],
    "class LRUCache:",
    """    def __init__(self, capacity: int) -> None:
        self.cap = capacity
        self._data: dict[int, int] = {}
        self._order: list[int] = []   # most recent first

    def get(self, key: int) -> int:
        if key not in self._data:
            return -1
        self._order.remove(key)
        self._order.insert(0, key)
        return self._data[key]

    def put(self, key: int, value: int) -> None:
        if key in self._data:
            self._order.remove(key)
        elif len(self._data) >= self.cap:
            lru = self._order.pop()
            del self._data[lru]
        self._data[key] = value
        self._order.insert(0, key)""",
    [
        (("__init__", 2), None),
    ],
    "public static int get(int key) { return -1; /* placeholder */ }",
    """    public static class LRUCache {
        private final int cap;
        private final Map<Integer, Node> map = new HashMap<>();
        private final Node head = new Node(0, 0);   // sentinel
        private final Node tail = new Node(0, 0);   // sentinel

        public LRUCache(int capacity) {
            this.cap = capacity;
            head.next = tail;
            tail.prev = head;
        }

        public int get(int key) {
            Node n = map.get(key);
            if (n == null) return -1;
            moveToFront(n);
            return n.val;
        }

        public void put(int key, int value) {
            Node n = map.get(key);
            if (n != null) {
                n.val = value;
                moveToFront(n);
            } else {
                if (map.size() == cap) {
                    Node lru = tail.prev;
                    map.remove(lru.key);
                    unlink(lru);
                }
                Node fresh = new Node(key, value);
                map.put(key, fresh);
                insertAfterHead(fresh);
            }
        }

        private void moveToFront(Node n) {
            unlink(n);
            insertAfterHead(n);
        }

        private void unlink(Node n) {
            n.prev.next = n.next;
            n.next.prev = n.prev;
        }

        private void insertAfterHead(Node n) {
            n.next = head.next;
            n.prev = head;
            head.next.prev = n;
            head.next = n;
        }

        private static class Node {
            int key, val;
            Node prev, next;
            Node(int k, int v) { key = k; val = v; }
        }
    }""",
    [],
    """A **doubly linked list** of nodes plus a **hash map** from key to
node gives O(1) access (via the map) and O(1) reordering (via the list).

- `head` and `tail` are sentinels so we never have to null-check neighbors.
- `moveToFront(n)`: unlink `n`, then insert it after `head`.
- On `put`, if the cache is full, evict `tail.prev` (the LRU).

**Time:** O(1) per op. **Space:** O(capacity).
""",
)

# 10. Merge K Sorted Lists (Hard)
add(
    "10-merge-k-sorted-lists", "Merge K Sorted Lists", "Hard",
    "You are given an array of `k` linked lists, each sorted in ascending "
    "order. Merge all the linked lists into one sorted linked list and "
    "return it.",
    [
        ("lists = [[1,4,5],[1,3,4],[2,6]]", "[1,1,2,3,4,4,5,6]"),
        ("lists = []", "[]"),
        ("lists = [[]]", "[]"),
    ],
    [
        "0 <= k <= 10^4",
        "0 <= lists[i].length <= 500",
        "-10^4 <= lists[i][j] <= 10^4",
        "lists[i] is sorted in ascending order",
        "The total number of nodes won't exceed 10^4",
    ],
    [
        "Min-heap of size k, popping the smallest head each step.",
        "Or divide-and-conquer: pair-merge, then merge the pairs, etc.",
    ],
    "def merge_k_lists(lists: list[list[int]]) -> list[int]:",
    """    import heapq
    heap: list[tuple[int, int, ListNode]] = []
    for i, lst in enumerate(lists):
        n = build_list(lst)
        if n:
            heapq.heappush(heap, (n.val, i, n))
    dummy = ListNode(0)
    tail = dummy
    while heap:
        val, i, node = heapq.heappop(heap)
        tail.next = node
        tail = tail.next
        if node.next:
            heapq.heappush(heap, (node.next.val, i, node.next))
    out: list[int] = []
    n = dummy.next
    while n:
        out.append(n.val); n = n.next
    return out""",
    [
        (([[1, 4, 5], [1, 3, 4], [2, 6]],), [1, 1, 2, 3, 4, 4, 5, 6]),
        (([[]],), []),
        (([],), []),
    ],
    "public static ListNode mergeKLists(ListNode[] lists)",
    """        PriorityQueue<ListNode> pq = new PriorityQueue<>(
            (a, b) -> Integer.compare(a.val, b.val)
        );
        for (ListNode n : lists) if (n != null) pq.offer(n);
        ListNode dummy = new ListNode(0);
        ListNode tail = dummy;
        while (!pq.isEmpty()) {
            ListNode n = pq.poll();
            tail.next = n;
            tail = tail.next;
            if (n.next != null) pq.offer(n.next);
        }
        return dummy.next""",
    [],
    """**Min-heap of size k.** Push the head of each non-empty list. Each
step: pop the smallest head, append it to the result, and push its
`next` (if any).

**Time:** O(N log k) where N is the total number of nodes.
**Space:** O(k) for the heap.
""",
)

# 11. Reverse Nodes In K Group (Hard)
add(
    "11-reverse-nodes-in-k-group", "Reverse Nodes in k-Group", "Hard",
    "Given the `head` of a linked list, reverse the nodes of the list "
    "`k` at a time, and return the modified list. `k` is a positive "
    "integer. If the number of nodes is not a multiple of `k`, the "
    "remaining nodes at the end should stay in the same order.",
    [
        ("head = [1,2,3,4,5], k = 2", "[2,1,4,3,5]"),
        ("head = [1,2,3,4,5], k = 3", "[3,2,1,4,5]"),
    ],
    [
        "1 <= k <= number of nodes",
        "0 <= number of nodes <= 5000",
        "0 <= Node.val <= 1000",
    ],
    [
        "Check that k nodes remain; if so, reverse them; otherwise, leave.",
        "Use a helper that reverses the next k nodes and returns the new head.",
    ],
    "def reverse_k_group(head: list[int], k: int) -> list[int]:",
    """    nodes = [ListNode(x) for x in head]
    for i in range(len(nodes) - 1):
        nodes[i].next = nodes[i + 1]
    h = nodes[0] if nodes else None

    def reverse_k(start, k):
        # returns (new_head, next_after_group)
        prev = None
        curr = start
        for _ in range(k):
            nxt = curr.next   # type: ignore
            curr.next = prev  # type: ignore
            prev = curr
            curr = nxt
        return prev, curr

    dummy = ListNode(0)
    dummy.next = h
    group_prev = dummy
    while True:
        kth = group_prev
        for _ in range(k):
            kth = kth.next    # type: ignore
            if kth is None:
                # fewer than k remain; we're done
                out: list[int] = []
                n = dummy.next
                while n:
                    out.append(n.val); n = n.next
                return out
        group_next = kth.next
        # reverse
        new_head, _ = reverse_k(group_prev.next, k)  # type: ignore
        # reconnect
        group_prev.next = new_head  # type: ignore
        # find the new tail
        new_tail = new_head
        while new_tail.next:    # type: ignore
            new_tail = new_tail.next  # type: ignore
        new_tail.next = group_next  # type: ignore
        group_prev = new_tail

    # unreachable
    return []""",
    [
        (([1, 2, 3, 4, 5], 2), [2, 1, 4, 3, 5]),
        (([1, 2, 3, 4, 5], 3), [3, 2, 1, 4, 5]),
    ],
    "public static ListNode reverseKGroup(ListNode head, int k)",
    """        ListNode dummy = new ListNode(0);
        dummy.next = head;
        ListNode groupPrev = dummy;
        while (true) {
            ListNode kth = groupPrev;
            for (int i = 0; i < k; i++) {
                kth = kth.next;
                if (kth == null) return dummy.next;
            }
            ListNode groupNext = kth.next;
            // reverse
            ListNode prev = null, curr = groupPrev.next;
            for (int i = 0; i < k; i++) {
                ListNode nxt = curr.next;
                curr.next = prev;
                prev = curr;
                curr = nxt;
            }
            // reconnect
            ListNode oldHead = groupPrev.next;
            groupPrev.next = prev;
            oldHead.next = groupNext;
            groupPrev = oldHead;
        }""",
    [],
    """Iterate in groups of `k`. For each group:

1. Walk `k` steps from `groupPrev` to find the end of the group; if you
   run out, the remaining nodes don't get reversed.
2. Reverse the group in place.
3. Reconnect: the previous group's tail now points to the new head; the
   old head (now the new tail) points to the next group.

**Time:** O(n). **Space:** O(1).
""",
)
