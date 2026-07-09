# GLOSSARY

A plain-English dictionary of every term used across the course. Each entry is
short; the modules go deep.

---

## Data structures

- **Array** — A contiguous block of memory holding elements of one type, indexed
  by position. `int[]` in Java, `list` in Python. O(1) random access.
- **List** — In Python, the dynamic array (`list`). In Java, the `List<T>`
  interface (most commonly `ArrayList<T>`).
- **String** — An immutable sequence of characters. In Java, prefer `StringBuilder`
  for in-place building; in Python, `str.join` or list-and-join.
- **Hash map / dictionary** — A key→value lookup table. Amortized O(1) insert,
  lookup, delete. Python `dict`, Java `HashMap<K, V>`.
- **Hash set** — A collection of unique items. O(1) membership test. Python
  `set`, Java `HashSet<T>`.
- **Stack** — LIFO container. `list`/`Collections.deque` (Java). Used for matching
  pairs, depth tracking, monotonic stacks.
- **Queue** — FIFO container. Python `collections.deque`, Java `ArrayDeque<T>`.
- **Deque** — Double-ended queue. O(1) push/pop at both ends.
- **Heap / priority queue** — A binary min-heap by default. O(log n) push/pop.
  Python `heapq`, Java `PriorityQueue<T>`.
- **Linked list** — Nodes with a value and a `next` pointer. O(1) insert at
  head; O(n) random access.
- **Tree** — A hierarchical structure. We deal mostly with **binary trees** (each
  node has up to two children).
- **Binary Search Tree (BST)** — A binary tree where left < node < right (in
  an ordered BST). In-order traversal is sorted.
- **Trie** — A prefix tree. Each edge is a character; each node marks a prefix.
  Used for word searches and autocompletion.
- **Graph** — A set of nodes (vertices) connected by edges. May be directed or
  undirected, weighted or unweighted. Represented as an adjacency list
  (most common) or adjacency matrix.

## Algorithmic patterns

- **Two pointers** — Walk through an array or string with two indices, often
  starting at opposite ends. Used for pair sums, palindromes, in-place edits.
- **Sliding window** — Maintain a contiguous subarray/substring "window" and
  slide it across the input. O(n) for problems that look O(n²) naively.
- **Binary search** — Halve the search space each step. Requires a *monotone*
  predicate (true→true→...→false, or vice versa). O(log n).
- **Prefix sum / prefix product** — Precompute cumulative sums/products for
  O(1) range queries. Watch out for overflow in Java `int`.
- **Monotonic stack** — A stack that maintains elements in strictly increasing
  or decreasing order. Used for "next greater element" problems.
- **Fast and slow pointers (Floyd)** — Two pointers moving at different speeds
  through a sequence. Detects cycles in O(1) space.
- **BFS (breadth-first search)** — Level-by-level traversal. Shortest path in
  unweighted graphs.
- **DFS (depth-first search)** — Recursive (or stack-based) traversal. Used for
  cycles, components, topological sort.
- **Dijkstra** — Shortest path in a graph with non-negative weights. O((V+E) log V)
  with a min-heap.
- **Union-Find (Disjoint Set Union, DSU)** — Tracks a partition of elements into
  sets. Near-O(1) with path compression + union by rank.
- **Topological sort** — Linear order of a DAG such that u→v means u comes
  before v. BFS (Kahn) or DFS variants.
- **Backtracking** — Build a solution incrementally and abandon ("prune")
  partial solutions that cannot lead to a valid answer.
- **Greedy** — Make the locally optimal choice at each step and hope (or prove)
  it's globally optimal. Works when the choice has a *matroid / exchange*
  property.
- **Dynamic programming (DP)** — Solve subproblems once, store the result,
  reuse. Top-down (memoized recursion) or bottom-up (iterative tables).
- **Bit manipulation** — Use bitwise operators (`&`, `|`, `^`, `<<`, `>>`) on
  integers. Useful for sets-of-small-integers and parity tricks.

## Complexity

- **Time complexity** — How the running time grows with input size `n`. Big-O
  notation drops constants and lower-order terms.
- **Space complexity** — How much *extra* memory the algorithm uses, ignoring
  the input itself.
- **Amortized** — Average cost per operation over a worst-case sequence.
  `list.append` in Python and `ArrayList.add` in Java are amortized O(1).
- **Auxiliary space** — The extra scratch space beyond the input.

## Interview concepts

- **Brute force** — The simplest correct solution, usually too slow. Always
  state it first; it's the fallback.
- **Optimization** — A faster solution, typically using a hash map, a sort, a
  heap, or a different traversal order.
- **State** — The data the algorithm "remembers" between steps. Explicit
  parameters, or implicit (recursion stack).
- **Memoization** — Caching function results so repeated calls return the
  cached value. Top-down DP.
- **Tabulation** — Filling a DP table bottom-up. Iterative DP.
- **In-place** — Mutating the input rather than allocating new structures.
  Often O(1) extra space.
- **Stable (sort)** — Equal elements retain their original relative order.
  Python `sort` is stable; Java's `Collections.sort` and `Arrays.sort` on
  object arrays are stable.
- **Top-K** — Find the k largest/smallest elements. Use a heap of size k for
  O(n log k) instead of O(n log n) full sort.
- **Two-pass** — A technique that scans the input twice (e.g. once to count,
  once to update).
