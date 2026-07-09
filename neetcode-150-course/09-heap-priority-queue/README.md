# Module 09 — Heap / Priority Queue 🔺

**Goal:** use heaps for top-k, scheduling, and median maintenance. ⏱️ ~4 h
· 🎯 Prereq: 08.

```
heap: O(log n) push/pop, O(1) peek — the right tool for "always process the smallest/largest"
```

---

## 1. What is a heap?

A heap is a **complete binary tree** (every level full, last level
left-aligned) where each parent is `≤` (min-heap) or `≥` (max-heap) its
children. It supports:

- `push` / `offer`: O(log n)
- `pop` / `poll`: O(log n)
- `peek`: O(1)

Heaps are stored as **arrays**: for node at index `i`, children are at
`2i+1` and `2i+2`.

In Python, `heapq` is a **min-heap**; use negation for max-heap. In Java,
`PriorityQueue` is a **min-heap** by default; pass `Comparator.reverseOrder()`
for a max-heap.

## 2. The 7 problems — easy → hard

| #  | Problem | Difficulty | Technique |
|----|---------|-----------|-----------|
| 01 | [Kth Largest in a Stream](./problems/01-kth-largest-element-in-a-stream/) | Easy | Min-heap of size k |
| 02 | [Last Stone Weight](./problems/02-last-stone-weight/) | Easy | Max-heap |
| 03 | [K Closest Points to Origin](./problems/03-k-closest-points-to-origin/) | Medium | Max-heap of size k on distance |
| 04 | [Kth Largest in an Array](./problems/04-kth-largest-element-in-an-array/) | Medium | Min-heap of size k (or quickselect) |
| 05 | [Task Scheduler](./problems/05-task-scheduler/) | Medium | Math on frequencies |
| 06 | [Design Twitter](./problems/06-design-twitter/) | Medium | Heap-merge k sorted lists |
| 07 | [Find Median from Data Stream](./problems/07-find-median-from-data-stream/) | Hard | Two heaps |

## 3. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Min-heap | `import heapq; heapq.heappush(h, x); x = heapq.heappop(h)` | `PriorityQueue<Integer> h = new PriorityQueue<>(); h.offer(x); x = h.poll();` |
| Max-heap | Push `-x` (negate) | `new PriorityQueue<>(Comparator.reverseOrder())` |
| `nlargest` | `heapq.nlargest(k, items, key=...)` | none — sort or build heap manually |
| `nsmallest` | `heapq.nsmallest(k, items, key=...)` | none |
| Custom comparator | Pass a `key` function | Pass a `Comparator` |

## 4. Common pitfalls

- **Wrong heap type.** Python's `heapq` is min; forget to negate for max.
  Java's `PriorityQueue` is min; forget `Comparator.reverseOrder()`.
- **Stale references.** Heap-merge-k-lists (Twitter) needs to remember
  *which* list each popped element came from so you can push the next.
- **Comparing `int / int` to `int / int`.** In Java, `/` is integer
  division; the median formula `peek() + peek() / 2.0` won't promote —
  use `2.0` explicitly to force floating point.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

heap · min-heap · max-heap · top-K · heap-merge · two-heaps pattern

**Next →** [Module 10: Backtracking](../10-backtracking/)
