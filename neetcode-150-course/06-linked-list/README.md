# Module 06 — Linked List 🔗

**Goal:** manipulate singly (and doubly) linked lists with confidence. ⏱️ ~6 h
· 🎯 Prereq: 05.

```
linked list: O(1) insert at head, O(n) random access, the right tool for "stream of nodes"
```

---

## 1. Why a linked list?

A linked list is a chain of `Node` objects, each holding a value and a
pointer to the next. **Insertion and deletion at known positions are O(1)**
(no shifting). The downside is **no random access** — finding the kth
element is O(k).

In interview code you usually don't use `java.util.LinkedList` (it's a
doubly linked list with extra overhead); you define a small `ListNode`
class.

## 2. The five techniques

1. **Dummy head.** A sentinel node before the real head. Removes the
   "first node is special" case.
2. **Slow/fast pointers.** Two pointers at different speeds — used for
   cycle detection, finding the middle, and kth-from-end.
3. **Reverse a list.** Three-pointer iterative: `prev`, `curr`, `next`.
4. **Merge two sorted lists.** Walk both with a tail pointer, picking the
   smaller front each step.
5. **Interleave two lists.** After splitting and reversing, weave them.

## 3. The 11 problems — easy → hard

| #  | Problem | Difficulty | Technique |
|----|---------|-----------|-----------|
| 01 | [Reverse Linked List](./problems/01-reverse-linked-list/) | Easy | Three-pointer reverse |
| 02 | [Merge Two Sorted Lists](./problems/02-merge-two-sorted-lists/) | Easy | Dummy + tail |
| 03 | [Reorder List](./problems/03-reorder-list/) | Medium | Find middle + reverse + interleave |
| 04 | [Remove Nth Node From End of List](./problems/04-remove-nth-node-from-end-of-list/) | Medium | Two pointers, dummy head |
| 05 | [Copy List With Random Pointer](./problems/05-copy-list-with-random-pointer/) | Medium | Interleave trick |
| 06 | [Add Two Numbers](./problems/06-add-two-numbers/) | Medium | Walk with carry |
| 07 | [Linked List Cycle](./problems/07-linked-list-cycle/) | Easy | Floyd's |
| 08 | [Find the Duplicate Number](./problems/08-find-the-duplicate-number/) | Medium | Floyd's on implicit LL |
| 09 | [LRU Cache](./problems/09-lru-cache/) | Medium | Hash map + doubly linked list |
| 10 | [Merge K Sorted Lists](./problems/10-merge-k-sorted-lists/) | Hard | Min-heap of heads |
| 11 | [Reverse Nodes in k-Group](./problems/11-reverse-nodes-in-k-group/) | Hard | Iterative group reverse |

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Class | `class ListNode: val, next` | `static class ListNode { int val; ListNode next; }` |
| Build list | `[Node(x) for x in arr]` + `for ... in zip` to set `next` | loop with `tail.next = new Node(x); tail = tail.next` |
| None vs null | `None` | `null` |
| Identity check | `a is b` | `a == b` (but be careful: use `==` for `Integer` boxed values) |
| `for n in list` | iterates nodes | need `for (ListNode n = head; n != null; n = n.next)` |
| `n.next` | `n.next` | `n.next` (same) |

## 5. Common pitfalls

- **Losing the rest of the list.** When you reverse or remove, save
  `n.next` *before* you change it.
- **Null checks.** Every walk needs a guard. Java won't auto-stop at
  `null`.
- **Forgetting the dummy.** Removing the first node requires a dummy.
- **Identity vs equality in Java.** `a == b` compares references for
  objects. Use `a.equals(b)` for content (e.g. `Integer`).

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

Then the [problems/](./problems/) in order.

## Key terms

dummy head · slow/fast pointers · Floyd's cycle · doubly linked list ·
hash map + linked list · min-heap of heads

**Next →** [Module 07: Trees](../07-trees/)
