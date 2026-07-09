# Module 11 — Graphs 🕸️

**Goal:** traverse, build, and analyze graphs. ⏱️ ~8 h · 🎯 Prereq: 10.

```
graph: BFS for shortest path in unweighted, DFS for connectivity, Union-Find for cycle detection
```

---

## 1. The four representations

| Form | When |
|------|------|
| **Adjacency list** (`dict[node, list]`) | Default. Most algorithms. |
| **Adjacency matrix** | Dense graphs, O(1) edge lookup. |
| **Edge list** (`[(u, v, w), ...]`) | Kruskal, certain problems. |
| **Implicit grid** | Number of Islands, Rotting Oranges, etc. |

In Python: `dict` or `defaultdict(list)`. In Java: `Map<Integer, List<Integer>>`.

## 2. The four patterns

| Pattern | Use |
|---------|-----|
| **DFS** (recursive or stack) | Connected components, cycle detection |
| **BFS** (queue) | Shortest path in unweighted graphs |
| **Multi-source BFS** | Walls and Gates, Rotting Oranges |
| **Union-Find** | Cycle detection, connected components |

## 3. The 13 problems — medium → hard

| #  | Problem | Difficulty | Pattern |
|----|---------|-----------|---------|
| 01 | [Number of Islands](./problems/01-number-of-islands/) | Medium | DFS on grid |
| 02 | [Max Area of Island](./problems/02-max-area-of-island/) | Medium | DFS, count area |
| 03 | [Clone Graph](./problems/03-clone-graph/) | Medium | DFS with `dict[old, new]` |
| 04 | [Walls and Gates](./problems/04-walls-and-gates/) | Medium | Multi-source BFS |
| 05 | [Rotting Oranges](./problems/05-rotting-oranges/) | Medium | Multi-source BFS, count levels |
| 06 | [Pacific Atlantic Water Flow](./problems/06-pacific-atlantic-water-flow/) | Medium | Reverse BFS from each ocean |
| 07 | [Surrounded Regions](./problems/07-surrounded-regions/) | Medium | Mark boundary, flip rest |
| 08 | [Course Schedule](./problems/08-course-schedule/) | Medium | Topological sort (Kahn) |
| 09 | [Course Schedule II](./problems/09-course-schedule-ii/) | Medium | Topological sort, record order |
| 10 | [Graph Valid Tree](./problems/10-graph-valid-tree/) | Medium | Union-Find, n-1 edges, no cycle |
| 11 | [Count Connected Components](./problems/11-number-of-connected-components-in-an-undirected-graph/) | Medium | Union-Find |
| 12 | [Redundant Connection](./problems/12-redundant-connection/) | Medium | Union-Find |
| 13 | [Word Ladder](./problems/13-word-ladder/) | Hard | BFS on implicit graph |

## 4. The Python / Java differences

| Concept | Python | Java |
|---------|--------|------|
| Adjacency list | `defaultdict(list)` | `Map<Integer, List<Integer>>` |
| BFS queue | `collections.deque` | `ArrayDeque<int[]>` or `ArrayDeque<Integer>` |
| Set | `set` | `HashSet<Integer>` |
| Grid (row, col) | `grid[r][c]` | `grid[r][c]` (same) |
| DFS in 4 dirs | inline 4 cases | inline or `int[][] dirs` |
| `INF` | `2**31 - 1` | `Integer.MAX_VALUE` |

## 5. Common pitfalls

- **Unvisited nodes.** Use a `set` / `boolean[]` to track visits.
- **Multi-source BFS level counting.** Use `for _ in range(len(q))` (or
  `int size = q.size()`) to process one level at a time.
- **Cycle detection in DFS.** Three colors: white (unvisited), gray (in
  recursion), black (done). A back-edge to a gray node is a cycle.
- **Union-Find without path compression is O(n log n) or worse.** Always
  compress.

---

## Do the lab

👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

BFS · DFS · multi-source BFS · Union-Find · topological sort ·
cycle detection · path compression

**Next →** [Module 12: Dynamic Programming](../12-dynamic-programming/)
