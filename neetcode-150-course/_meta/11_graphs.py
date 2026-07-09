"""Module 11 — Graphs problem catalog."""

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


# 1. Number of Islands (Medium)
add(
    "01-number-of-islands", "Number of Islands", "Medium",
    "Given an `m x n` 2D binary grid `grid` which represents a map of "
    "'1's (land) and '0's (water), return the number of islands. An "
    "island is surrounded by water and is formed by connecting adjacent "
    "lands horizontally or vertically.",
    [
        ("grid = [['1','1','1','1','0'],['1','1','0','1','0'],"
         "['1','1','0','0','0'],['0','0','0','0','0']]", "1"),
        ("grid = [['1','1','0','0','0'],['1','1','0','0','0'],"
         "['0','0','1','0','0'],['0','0','0','1','1']]", "3"),
    ],
    [
        "m == grid.length, n == grid[i].length",
        "1 <= m, n <= 300",
        "grid[i][j] is '0' or '1'",
    ],
    [
        "Iterate the grid; on each unvisited '1', DFS to mark the whole "
        "island and increment count.",
    ],
    "def num_islands(grid: list[list[str]]) -> int:",
    """    if not grid: return 0
    rows, cols = len(grid), len(grid[0])

    def dfs(r: int, c: int) -> None:
        if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '#'
        dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)
    return count""",
    [
        (([["1","1","1","1","0"],["1","1","0","1","0"],["1","1","0","0","0"],["0","0","0","0","0"]],), 1),
        (([["1","1","0","0","0"],["1","1","0","0","0"],["0","0","1","0","0"],["0","0","0","1","1"]],), 3),
    ],
    "public static int numIslands(char[][] grid)",
    """        if (grid.length == 0) return 0;
        int rows = grid.length, cols = grid[0].length;
        int count = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == '1') { count++; dfs(grid, r, c); }
            }
        }
        return count;
    }

    private static void dfs(char[][] grid, int r, int c) {
        if (r < 0 || c < 0 || r >= grid.length || c >= grid[0].length || grid[r][c] != '1') return;
        grid[r][c] = '#';
        dfs(grid, r + 1, c); dfs(grid, r - 1, c);
        dfs(grid, r, c + 1); dfs(grid, r, c - 1);""",
    [],
    """Iterate the grid. On each unvisited `'1'`, increment the count
and DFS-mark the connected component (replace `'1'` with `'#'`).

**Time:** O(m·n). **Space:** O(m·n) for the recursion in the worst case
(degenerate single-line island).
""",
)

# 2. Max Area of Island (Medium)
add(
    "02-max-area-of-island", "Max Area of Island", "Medium",
    "You are given an `m x n` binary matrix `grid`. An island is a group "
    "of `1`s connected 4-directionally. The **area** of an island is the "
    "number of cells with a value of 1 in it. Return the maximum area of "
    "an island in `grid`. If there is no island, return 0.",
    [
        ("grid = [[0,0,1,0,0,0,0,1,0,0,0,0,0],"
         "[0,0,0,0,0,0,0,1,1,1,0,0,0],"
         "[0,1,1,0,1,0,0,0,0,0,0,0,0],"
         "[0,1,0,0,1,1,0,0,1,0,1,0,0],"
         "[0,1,0,0,1,1,0,0,1,1,1,0,0],"
         "[0,0,0,0,0,0,0,0,0,0,1,0,0],"
         "[0,0,0,0,0,0,0,1,2,4,4,0,0]]", "6"),
    ],
    [
        "m == grid.length, n == grid[i].length",
        "1 <= m, n <= 50",
        "grid[i][j] is 0 or 1",
    ],
    [
        "Same DFS as Number of Islands, but return the size of each "
        "island.",
    ],
    "def max_area_of_island(grid: list[list[int]]) -> int:",
    """    rows, cols = len(grid), len(grid[0])

    def dfs(r: int, c: int) -> int:
        if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != 1:
            return 0
        grid[r][c] = 0
        return 1 + dfs(r + 1, c) + dfs(r - 1, c) + dfs(r, c + 1) + dfs(r, c - 1)

    best = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 1:
                best = max(best, dfs(r, c))
    return best""",
    [
        (([[0,0,1,0,0,0,0,1,0,0,0,0,0],[0,0,0,0,0,0,0,1,1,1,0,0,0],[0,1,1,0,1,0,0,0,0,0,0,0,0],[0,1,0,0,1,1,0,0,1,0,1,0,0],[0,1,0,0,1,1,0,0,1,1,1,0,0],[0,0,0,0,0,0,0,0,0,0,1,0,0],[0,0,0,0,0,0,0,1,2,4,4,0,0]],), 6),
    ],
    "public static int maxAreaOfIsland(int[][] grid)",
    """        int rows = grid.length, cols = grid[0].length;
        int best = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 1) best = Math.max(best, dfs(grid, r, c));
            }
        }
        return best;
    }

    private static int dfs(int[][] grid, int r, int c) {
        if (r < 0 || c < 0 || r >= grid.length || c >= grid[0].length || grid[r][c] != 1) return 0;
        grid[r][c] = 0;
        return 1 + dfs(grid, r + 1, c) + dfs(grid, r - 1, c) + dfs(grid, r, c + 1) + dfs(grid, r, c - 1);""",
    [],
    """Same as Number of Islands, but the DFS returns the area. Track
the maximum.

**Time:** O(m·n). **Space:** O(m·n) recursion.
""",
)

# 3. Clone Graph (Medium)
add(
    "03-clone-graph", "Clone Graph", "Medium",
    "Given a reference of a node in a **connected** undirected graph, "
    "return a deep copy (clone) of the graph. Each node in the graph "
    "contains a value (`int`) and a list (`List[Node]`) of its neighbors.",
    [
        ("adjList = [[2,4],[1,3],[2,4],[1,3]]", "Same structure, new nodes"),
    ],
    [
        "0 <= number of nodes <= 100",
        "1 <= Node.val <= 100",
    ],
    [
        "DFS, building a `dict[old, new]` as you go. Return `new_node` "
        "for each `old_node`.",
    ],
    "def clone_graph(adj: list[list[int]]) -> int:",
    """    # Build the graph from adjacency list, clone it, return the count of distinct nodes
    g = build_graph(adj)
    if g is None: return 0
    cloned: dict[int, GraphNode] = {}

    def dfs(n):
        if n.val in cloned:
            return cloned[n.val]
        copy = GraphNode(n.val)
        cloned[n.val] = copy
        copy.neighbors = [dfs(nb) for nb in n.neighbors]
        return copy

    dfs(g)
    return len(cloned)""",
    [
        (([[2], [1]],), 2),
        (([[2, 3], [1, 3], [1, 2]],), 3),
        (([],), 0),
    ],
    "public static int cloneGraph(int[][] adj)",
    """        if (adj == null || adj.length == 0) return 0;
        GraphNode[] nodes = new GraphNode[adj.length + 1];
        for (int i = 1; i <= adj.length; i++) nodes[i] = new GraphNode(i);
        for (int i = 1; i <= adj.length; i++) {
            for (int j : adj[i - 1]) nodes[i].neighbors.add(nodes[j]);
        }
        Map<Integer, GraphNode> cloned = new HashMap<>();
        dfs(nodes[1], cloned);
        return cloned.size();
    }

    private static GraphNode dfs(GraphNode n, Map<Integer, GraphNode> cloned) {
        if (cloned.containsKey(n.val)) return cloned.get(n.val);
        GraphNode copy = new GraphNode(n.val);
        cloned.put(n.val, copy);
        copy.neighbors = new ArrayList<>();
        for (GraphNode nb : n.neighbors) copy.neighbors.add(dfs(nb, cloned));
        return copy;""",
    [],
    """DFS with a `dict[old_id, new_node]`. When we revisit a node, we
return the already-created copy — this prevents infinite recursion in
the presence of cycles.

**Time:** O(V + E). **Space:** O(V) for the map and recursion.
""",
)

# 4. Walls and Gates (Medium)
add(
    "04-walls-and-gates", "Walls and Gates", "Medium",
    "You are given an `m x n` grid `rooms` initialized with these three "
    "possible values: -1 (a wall or obstacle), 0 (a gate), and INF (an "
    "empty room). Fill each empty room with the distance to its nearest "
    "gate. If it is impossible to reach a gate, leave it as INF.",
    [
        ("rooms = [[2147483647,-1,0,2147483647],"
         "[2147483647,2147483647,2147483647,-1],"
         "[2147483647,-1,2147483647,-1],"
         "[0,-1,2147483647,2147483647]]",
         "rooms with each empty cell = distance to nearest 0"),
    ],
    [
        "m == rooms.length, n == rooms[i].length",
        "1 <= m, n <= 250",
        "rooms[i][j] is -1, 0, or 2^31 - 1",
    ],
    [
        "Multi-source BFS from all gates simultaneously.",
    ],
    "def walls_and_gates(rooms: list[list[int]]) -> list[list[int]]:",
    """    INF = 2 ** 31 - 1
    rows, cols = len(rooms), len(rooms[0])
    from collections import deque
    q: deque[tuple[int, int]] = deque()
    for r in range(rows):
        for c in range(cols):
            if rooms[r][c] == 0:
                q.append((r, c))
    while q:
        r, c = q.popleft()
        d = rooms[r][c]
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols and rooms[nr][nc] == INF:
                rooms[nr][nc] = d + 1
                q.append((nr, nc))
    return rooms""",
    [
        (([[2147483647, -1, 0, 2147483647], [2147483647, 2147483647, 2147483647, -1], [2147483647, -1, 2147483647, -1], [0, -1, 2147483647, 2147483647]],), [[3, -1, 0, 1], [2, 2, 1, -1], [1, -1, 2, -1], [0, -1, 3, 4]]),
    ],
    "public static void wallsAndGates(int[][] rooms)",
    """        int rows = rooms.length, cols = rooms[0].length;
        Deque<int[]> q = new ArrayDeque<>();
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (rooms[r][c] == 0) q.offer(new int[]{r, c});
            }
        }
        while (!q.isEmpty()) {
            int[] cur = q.poll();
            int d = rooms[cur[0]][cur[1]];
            int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
            for (int[] dir : dirs) {
                int nr = cur[0] + dir[0], nc = cur[1] + dir[1];
                if (nr < 0 || nc < 0 || nr >= rows || nc >= cols) continue;
                if (rooms[nr][nc] != Integer.MAX_VALUE) continue;
                rooms[nr][nc] = d + 1;
                q.offer(new int[]{nr, nc});
            }
        }""",
    [],
    """Multi-source BFS. Start a queue with all gates; BFS out from
each, writing the distance to each empty cell. The first time we
visit a cell, the distance is the shortest.

**Time:** O(m·n). **Space:** O(m·n) for the queue.
""",
)

# 5. Rotting Oranges (Medium)
add(
    "05-rotting-oranges", "Rotting Oranges", "Medium",
    "You are given an `m x n` grid where each cell can have one of three "
    "values: 0 (empty), 1 (fresh orange), or 2 (rotten orange). Every "
    "minute, any fresh orange 4-directionally adjacent to a rotten "
    "orange becomes rotten. Return the minimum number of minutes that "
    "must elapse until no cell with a fresh orange exists. If impossible, "
    "return -1.",
    [
        ("grid = [[2,1,1],[1,1,0],[0,1,1]]", "4"),
        ("grid = [[2,1,1],[0,1,1],[1,0,1]]", "-1"),
    ],
    [
        "m == grid.length, n == grid[i].length",
        "1 <= m, n <= 10",
        "grid[i][j] is 0, 1, or 2",
    ],
    [
        "Multi-source BFS from all rotten oranges. Count the BFS levels "
        "until no fresh remain.",
    ],
    "def oranges_rotting(grid: list[list[int]]) -> int:",
    """    from collections import deque
    rows, cols = len(grid), len(grid[0])
    q: deque[tuple[int, int]] = deque()
    fresh = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == 2:
                q.append((r, c))
            elif grid[r][c] == 1:
                fresh += 1
    minutes = 0
    while q and fresh:
        for _ in range(len(q)):
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and grid[nr][nc] == 1:
                    grid[nr][nc] = 2
                    fresh -= 1
                    q.append((nr, nc))
        minutes += 1
    return minutes if fresh == 0 else -1""",
    [
        (([[2, 1, 1], [1, 1, 0], [0, 1, 1]],), 4),
        (([[2, 1, 1], [0, 1, 1], [1, 0, 1]],), -1),
        (([[0, 2]],), 0),
    ],
    "public static int orangesRotting(int[][] grid)",
    """        int rows = grid.length, cols = grid[0].length;
        Deque<int[]> q = new ArrayDeque<>();
        int fresh = 0;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (grid[r][c] == 2) q.offer(new int[]{r, c});
                else if (grid[r][c] == 1) fresh++;
            }
        }
        int minutes = 0;
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        while (!q.isEmpty() && fresh > 0) {
            int size = q.size();
            for (int i = 0; i < size; i++) {
                int[] cur = q.poll();
                for (int[] d : dirs) {
                    int nr = cur[0] + d[0], nc = cur[1] + d[1];
                    if (nr < 0 || nc < 0 || nr >= rows || nc >= cols) continue;
                    if (grid[nr][nc] != 1) continue;
                    grid[nr][nc] = 2;
                    fresh--;
                    q.offer(new int[]{nr, nc});
                }
            }
            minutes++;
        }
        return fresh == 0 ? minutes : -1;
    }""",
    [],
    """Multi-source BFS. Each "level" of the BFS represents one minute.
At each level, all the fresh oranges adjacent to current rotten ones
become rotten. If we exit the loop and `fresh > 0`, it's impossible.

**Time:** O(m·n). **Space:** O(m·n).
""",
)

# 6. Pacific Atlantic Water Flow (Medium)
add(
    "06-pacific-atlantic-water-flow", "Pacific Atlantic Water Flow", "Medium",
    "There is an `m x n` rectangular island that borders both the **Pacific "
    "Ocean** and the **Atlantic Ocean**. The Pacific Ocean touches the "
    "island's left and top edges, and the Atlantic Ocean touches the "
    "island's right and bottom edges. The island is partitioned into a "
    "grid of square cells. You are given an `m x n` integer matrix "
    "`heights` where `heights[r][c]` represents the height above sea "
    "level of the cell at coordinates `(r, c)`. The island receives a lot "
    "of rain, and the rain water can flow to neighboring cells directly "
    "north, south, east, and west if the neighboring cell's height is "
    "less than or equal to the current cell's height. Water can flow "
    "from any cell adjacent to an ocean into that ocean. Return a 2D list "
    "of grid coordinates `result` where `result[i] = [ri, ci]` denotes "
    "that rain water can flow from cell `(ri, ci)` to **both** the "
    "Pacific and Atlantic oceans.",
    [
        ("heights = [[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],"
         "[6,7,1,4,5],[5,1,1,2,4]]",
         "[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]"),
    ],
    [
        "m == heights.length, n == heights[i].length",
        "1 <= m, n <= 200",
        "0 <= heights[r][c] <= 10^5",
    ],
    [
        "Reverse thinking: BFS/DFS from each ocean inward, marking cells "
        "that can reach the ocean. The intersection is the answer.",
    ],
    "def pacific_atlantic(heights: list[list[int]]) -> list[list[int]]:",
    """    rows, cols = len(heights), len(heights[0])
    from collections import deque

    def bfs(starts: list[tuple[int, int]]) -> set[tuple[int, int]]:
        reachable: set[tuple[int, int]] = set(starts)
        q: deque[tuple[int, int]] = deque(starts)
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in reachable and heights[nr][nc] >= heights[r][c]:
                    reachable.add((nr, nc))
                    q.append((nr, nc))
        return reachable

    pacific = [(0, c) for c in range(cols)] + [(r, 0) for r in range(1, rows)]
    atlantic = [(rows - 1, c) for c in range(cols)] + [(r, cols - 1) for r in range(rows - 1)]
    pac = bfs(pacific)
    atl = bfs(atlantic)
    return [[r, c] for r, c in sorted(pac & atl)]""",
    [
        (([[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]],), [[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]),
    ],
    "public static List<List<Integer>> pacificAtlantic(int[][] heights)",
    """        int rows = heights.length, cols = heights[0].length;
        boolean[][] pac = new boolean[rows][cols];
        boolean[][] atl = new boolean[rows][cols];
        Deque<int[]> q = new ArrayDeque<>();
        for (int c = 0; c < cols; c++) { q.offer(new int[]{0, c}); pac[0][c] = true; }
        for (int r = 1; r < rows; r++) { q.offer(new int[]{r, 0}); pac[r][0] = true; }
        bfs(heights, q, pac);
        q.clear();
        for (int c = 0; c < cols; c++) { q.offer(new int[]{rows - 1, c}); atl[rows - 1][c] = true; }
        for (int r = 0; r < rows - 1; r++) { q.offer(new int[]{r, cols - 1}); atl[r][cols - 1] = true; }
        bfs(heights, q, atl);
        List<List<Integer>> out = new ArrayList<>();
        for (int r = 0; r < rows; r++) for (int c = 0; c < cols; c++) {
            if (pac[r][c] && atl[r][c]) out.add(List.of(r, c));
        }
        return out;
    }

    private static void bfs(int[][] h, Deque<int[]> q, boolean[][] reach) {
        int[][] dirs = {{1,0},{-1,0},{0,1},{0,-1}};
        while (!q.isEmpty()) {
            int[] cur = q.poll();
            for (int[] d : dirs) {
                int nr = cur[0] + d[0], nc = cur[1] + d[1];
                if (nr < 0 || nc < 0 || nr >= h.length || nc >= h[0].length) continue;
                if (reach[nr][nc]) continue;
                if (h[nr][nc] < h[cur[0]][cur[1]]) continue;
                reach[nr][nc] = true;
                q.offer(new int[]{nr, nc});
            }
        }
    }""",
    [],
    """**Reverse the problem.** BFS from the Pacific (top + left edges)
inward, marking all cells that can flow to it. Do the same for
Atlantic (bottom + right). The intersection is the answer.

**Time:** O(m·n). **Space:** O(m·n).
""",
)

# 7. Surrounded Regions (Medium)
add(
    "07-surrounded-regions", "Surrounded Regions", "Medium",
    "Given an `m x n` matrix `board` containing 'X' and 'O', capture all "
    "regions that are 4-directionally surrounded by 'X'. A region is "
    "captured by flipping all 'O's into 'X's in that surrounded region.",
    [
        ("board = [['X','X','X','X'],['X','O','O','X'],"
         "['X','X','O','X'],['X','O','X','X']]",
         "[['X','X','X','X'],['X','X','X','X'],['X','X','X','X'],['X','O','X','X']]"),
    ],
    [
        "m == board.length, n == board[i].length",
        "1 <= m, n <= 200",
        "board[i][j] is 'X' or 'O'",
    ],
    [
        "Mark boundary 'O's and their connected 'O's as unsurroundable. "
        "Flip the rest.",
    ],
    "def solve(board: list[list[str]]) -> list[list[str]]:",
    """    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int) -> None:
        if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != 'O':
            return
        board[r][c] = '#'
        dfs(r + 1, c); dfs(r - 1, c); dfs(r, c + 1); dfs(r, c - 1)

    for r in range(rows):
        for c in (0, cols - 1):
            if board[r][c] == 'O':
                dfs(r, c)
    for c in range(cols):
        for r in (0, rows - 1):
            if board[r][c] == 'O':
                dfs(r, c)
    for r in range(rows):
        for c in range(cols):
            if board[r][c] == 'O':
                board[r][c] = 'X'
            elif board[r][c] == '#':
                board[r][c] = 'O'
    return board""",
    [
        (([["X","X","X","X"],["X","O","O","X"],["X","X","O","X"],["X","O","X","X"]],), [["X","X","X","X"],["X","X","X","X"],["X","X","X","X"],["X","O","X","X"]]),
    ],
    "public static void solve(char[][] board)",
    """        int rows = board.length, cols = board[0].length;
        for (int r = 0; r < rows; r++) {
            if (board[r][0] == 'O') dfs(board, r, 0);
            if (board[r][cols - 1] == 'O') dfs(board, r, cols - 1);
        }
        for (int c = 0; c < cols; c++) {
            if (board[0][c] == 'O') dfs(board, 0, c);
            if (board[rows - 1][c] == 'O') dfs(board, rows - 1, c);
        }
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (board[r][c] == 'O') board[r][c] = 'X';
                else if (board[r][c] == '#') board[r][c] = 'O';
            }
        }
    }

    private static void dfs(char[][] board, int r, int c) {
        if (r < 0 || c < 0 || r >= board.length || c >= board[0].length || board[r][c] != 'O') return;
        board[r][c] = '#';
        dfs(board, r + 1, c); dfs(board, r - 1, c);
        dfs(board, r, c + 1); dfs(board, r, c - 1);""",
    [],
    """Mark all 'O's connected to the boundary with `'#'`. Then sweep
the board: `'O'` (surrounded) becomes `'X'`; `'#'` (boundary) becomes
`'O'`.

**Time:** O(m·n). **Space:** O(m·n) recursion.
""",
)

# 8. Course Schedule (Medium)
add(
    "08-course-schedule", "Course Schedule", "Medium",
    "There are a total of `numCourses` courses you have to take, labeled "
    "from `0` to `numCourses - 1`. You are given an array `prerequisites` "
    "where `prerequisites[i] = [ai, bi]` indicates that you must take "
    "course `bi` first if you want to take course `ai`. Return `True` if "
    "you can finish all courses. Otherwise, return `False`.",
    [
        ("numCourses = 2, prerequisites = [[1,0]]", "True"),
        ("numCourses = 2, prerequisites = [[1,0],[0,1]]", "False"),
    ],
    [
        "1 <= numCourses <= 2000",
        "0 <= prerequisites.length <= 5000",
        "prerequisites[i].length == 2",
        "0 <= ai, bi < numCourses",
        "All the pairs prerequisites[i] are unique",
    ],
    [
        "Detect a cycle in the directed graph of prerequisites.",
    ],
    "def can_finish(num_courses: int, prerequisites: list[list[int]]) -> bool:",
    """    from collections import defaultdict, deque
    g: dict[int, list[int]] = defaultdict(list)
    indeg = [0] * num_courses
    for a, b in prerequisites:
        g[b].append(a)
        indeg[a] += 1
    q: deque[int] = deque(i for i in range(num_courses) if indeg[i] == 0)
    taken = 0
    while q:
        c = q.popleft()
        taken += 1
        for nb in g[c]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                q.append(nb)
    return taken == num_courses""",
    [
        ((2, [[1, 0]]), True),
        ((2, [[1, 0], [0, 1]]), False),
        ((3, [[1, 0], [2, 1]]), True),
    ],
    "public static boolean canFinish(int numCourses, int[][] prerequisites)",
    """        List<List<Integer>> g = new ArrayList<>();
        int[] indeg = new int[numCourses];
        for (int i = 0; i < numCourses; i++) g.add(new ArrayList<>());
        for (int[] p : prerequisites) {
            g.get(p[1]).add(p[0]);
            indeg[p[0]]++;
        }
        Deque<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < numCourses; i++) if (indeg[i] == 0) q.offer(i);
        int taken = 0;
        while (!q.isEmpty()) {
            int c = q.poll();
            taken++;
            for (int nb : g.get(c)) {
                if (--indeg[nb] == 0) q.offer(nb);
            }
        }
        return taken == numCourses;""",
    [],
    """Kahn's algorithm (topological sort via BFS). If we can take all
courses, there's no cycle. Count how many we actually took.

**Time:** O(V + E). **Space:** O(V + E).
""",
)

# 9. Course Schedule II (Medium)
add(
    "09-course-schedule-ii", "Course Schedule II", "Medium",
    "Same problem as Course Schedule, but return the ordering of courses "
    "you should take to finish all courses. If there are many valid "
    "answers, return **any** of them. If it's impossible, return an "
    "empty array.",
    [
        ("numCourses = 2, prerequisites = [[1,0]]", "[0, 1]"),
        ("numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]",
         "[0, 2, 1, 3] or [0, 1, 2, 3]"),
    ],
    [
        "Same as Course Schedule",
    ],
    [
        "Same as Course Schedule, but record the order.",
    ],
    "def find_order(num_courses: int, prerequisites: list[list[int]]) -> list[int]:",
    """    from collections import defaultdict, deque
    g: dict[int, list[int]] = defaultdict(list)
    indeg = [0] * num_courses
    for a, b in prerequisites:
        g[b].append(a)
        indeg[a] += 1
    q: deque[int] = deque(i for i in range(num_courses) if indeg[i] == 0)
    order: list[int] = []
    while q:
        c = q.popleft()
        order.append(c)
        for nb in g[c]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                q.append(nb)
    return order if len(order) == num_courses else []""",
    [
        ((2, [[1, 0]]), [0, 1]),
        ((4, [[1, 0], [2, 0], [3, 1], [3, 2]]), [0, 1, 2, 3]),
    ],
    "public static int[] findOrder(int numCourses, int[][] prerequisites)",
    """        List<List<Integer>> g = new ArrayList<>();
        int[] indeg = new int[numCourses];
        for (int i = 0; i < numCourses; i++) g.add(new ArrayList<>());
        for (int[] p : prerequisites) {
            g.get(p[1]).add(p[0]);
            indeg[p[0]]++;
        }
        Deque<Integer> q = new ArrayDeque<>();
        for (int i = 0; i < numCourses; i++) if (indeg[i] == 0) q.offer(i);
        int[] order = new int[numCourses];
        int idx = 0;
        while (!q.isEmpty()) {
            int c = q.poll();
            order[idx++] = c;
            for (int nb : g.get(c)) if (--indeg[nb] == 0) q.offer(nb);
        }
        return idx == numCourses ? order : new int[0];""",
    [],
    """Same as Course Schedule, but record the order in which we pop
from the queue.

**Time:** O(V + E). **Space:** O(V + E).
""",
)

# 10. Graph Valid Tree (Medium)
add(
    "10-graph-valid-tree", "Graph Valid Tree", "Medium",
    "You have a graph of `n` nodes labeled from `0` to `n - 1`. You are "
    "given an integer `n` and a list of `edges` where `edges[i] = [ai, bi]` "
    "indicates that there is an undirected edge between nodes `ai` and "
    "`bi` in the graph. Return `True` if the edges of the given graph "
    "make up a valid tree, and `False` otherwise.",
    [
        ("n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]", "True"),
        ("n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]", "False"),
    ],
    [
        "1 <= n <= 2000",
        "0 <= edges.length <= n * (n - 1) / 2",
    ],
    [
        "A graph is a tree iff (a) it has exactly n-1 edges and (b) it's "
        "connected.",
    ],
    "def valid_tree(n: int, edges: list[list[int]]) -> bool:",
    """    if len(edges) != n - 1:
        return False
    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return False
        parent[ra] = rb
    return True""",
    [
        ((5, [[0, 1], [0, 2], [0, 3], [1, 4]]), True),
        ((5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]), False),
    ],
    "public static boolean validTree(int n, int[][] edges)",
    """        if (edges.length != n - 1) return false;
        int[] parent = new int[n];
        for (int i = 0; i < n; i++) parent[i] = i;
        for (int[] e : edges) {
            int ra = find(parent, e[0]);
            int rb = find(parent, e[1]);
            if (ra == rb) return false;
            parent[ra] = rb;
        }
        return true;
    }

    private static int find(int[] parent, int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;""",
    [],
    """A graph is a tree iff (a) exactly n-1 edges and (b) no cycle.
Union-Find detects cycles as we add edges.

**Time:** O(V + E · α(V)). **Space:** O(V).
""",
)

# 11. Number of Connected Components in an Undirected Graph (Medium)
add(
    "11-number-of-connected-components-in-an-undirected-graph",
    "Number of Connected Components in an Undirected Graph", "Medium",
    "You have a graph of `n` nodes labeled from `0` to `n - 1`. You are "
    "given an integer `n` and an array `edges` where `edges[i] = [ai, "
    "bi]` indicates that there is an edge between `ai` and `bi` in the "
    "graph. Return the number of connected components in the graph.",
    [
        ("n = 5, edges = [[0,1],[1,2],[3,4]]", "2"),
        ("n = 5, edges = [[0,1],[1,2],[2,3],[3,4]]", "1"),
    ],
    [
        "1 <= n <= 2000",
        "0 <= edges.length <= n * (n - 1) / 2",
    ],
    [
        "Union-Find: each edge unites two components. The final count is "
        "the number of distinct roots.",
    ],
    "def count_components(n: int, edges: list[list[int]]) -> int:",
    """    parent = list(range(n))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb
    return len({find(i) for i in range(n)})""",
    [
        ((5, [[0, 1], [1, 2], [3, 4]]), 2),
        ((5, [[0, 1], [1, 2], [2, 3], [3, 4]]), 1),
    ],
    "public static int countComponents(int n, int[][] edges)",
    """        int[] parent = new int[n];
        for (int i = 0; i < n; i++) parent[i] = i;
        for (int[] e : edges) {
            int ra = find(parent, e[0]);
            int rb = find(parent, e[1]);
            if (ra != rb) parent[ra] = rb;
        }
        java.util.Set<Integer> roots = new java.util.HashSet<>();
        for (int i = 0; i < n; i++) roots.add(find(parent, i));
        return roots.size();
    }

    private static int find(int[] parent, int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;""",
    [],
    """Union-Find. Each edge unites two components. The number of
distinct roots at the end is the answer.

**Time:** O(V + E · α(V)). **Space:** O(V).
""",
)

# 12. Redundant Connection (Medium)
add(
    "12-redundant-connection", "Redundant Connection", "Medium",
    "In this problem, a tree is an undirected graph that is connected "
    "and has no cycles. You are given a graph that started as a tree "
    "with `n` nodes labeled from `1` to `n`, with one additional edge "
    "added. The added edge has two different vertices chosen from `1` to "
    "`n`, and was not an edge that already existed. The graph is "
    "represented as an array `edges` of length `n` where `edges[i] = [ai, "
    "bi]` indicates that there is an edge between nodes `ai` and `bi` in "
    "the graph. Return an edge that can be removed so that the resulting "
    "graph is a tree with `n` nodes. If there are multiple answers, "
    "return the edge that appears **last** in the input.",
    [
        ("edges = [[1,2],[1,3],[2,3]]", "[2, 3]"),
        ("edges = [[1,2],[2,3],[3,4],[1,4],[1,5]]", "[1, 4]"),
    ],
    [
        "n == edges.length",
        "3 <= n <= 1000",
        "edges[i].length == 2",
        "1 <= ai < bi <= edges.length",
        "There are no repeated edges",
        "The given graph is connected",
    ],
    [
        "Union-Find: the first edge whose endpoints are already in the "
        "same component is the redundant one.",
    ],
    "def find_redundant_connection(edges: list[list[int]]) -> list[int]:",
    """    n = len(edges)
    parent = list(range(n + 1))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in edges:
        ra, rb = find(a), find(b)
        if ra == rb:
            return [a, b]
        parent[ra] = rb
    return []""",
    [
        (([[1, 2], [1, 3], [2, 3]],), [2, 3]),
        (([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]],), [1, 4]),
    ],
    "public static int[] findRedundantConnection(int[][] edges)",
    """        int n = edges.length;
        int[] parent = new int[n + 1];
        for (int i = 1; i <= n; i++) parent[i] = i;
        for (int[] e : edges) {
            int ra = find(parent, e[0]);
            int rb = find(parent, e[1]);
            if (ra == rb) return e;
            parent[ra] = rb;
        }
        return new int[0];
    }

    private static int find(int[] parent, int x) {
        while (parent[x] != x) {
            parent[x] = parent[parent[x]];
            x = parent[x];
        }
        return x;""",
    [],
    """Union-Find. The first edge whose endpoints are already in the
same component creates a cycle — that's the redundant edge.

**Time:** O(n · α(n)). **Space:** O(n).
""",
)

# 13. Word Ladder (Hard)
add(
    "13-word-ladder", "Word Ladder", "Hard",
    "A **transformation sequence** from word `beginWord` to word "
    "`endWord` using a dictionary `wordList` is a sequence of words "
    "`beginWord -> s1 -> s2 -> ... -> sk` such that: every adjacent pair "
    "differs by a single letter, and every `si` (for 1 <= i <= k) is in "
    "`wordList`. Given two words, `beginWord` and `endWord`, and a "
    "dictionary `wordList`, return the **number of words** in the "
    "**shortest transformation sequence** from `beginWord` to `endWord`, "
    "or 0 if no such sequence exists.",
    [
        ("beginWord = 'hit', endWord = 'cog', "
         "wordList = ['hot','dot','dog','lot','log','cog']", "5"),
        ("beginWord = 'hit', endWord = 'cog', "
         "wordList = ['hot','dot','dog','lot','log']", "0"),
    ],
    [
        "1 <= len(beginWord) == len(endWord) <= 10",
        "1 <= len(wordList) <= 5000",
        "All words consist of lowercase English letters",
    ],
    [
        "BFS from `beginWord`. Two optimization tricks: (1) convert all "
        "words to lowercase and use a set; (2) for each word, try all "
        "single-letter substitutions.",
        "Better: precompute adjacency using intermediate 'wildcard' "
        "patterns (e.g. 'h_t' matches 'hot' and 'hat').",
    ],
    "def ladder_length(begin_word: str, end_word: str, word_list: list[str]) -> int:",
    """    word_set = set(word_list)
    if end_word not in word_set:
        return 0
    from collections import deque
    q: deque[tuple[str, int]] = deque([(begin_word, 1)])
    visited = {begin_word}
    L = len(begin_word)
    while q:
        word, d = q.popleft()
        if word == end_word:
            return d
        for i in range(L):
            for c in 'abcdefghijklmnopqrstuvwxyz':
                if c == word[i]:
                    continue
                nw = word[:i] + c + word[i + 1:]
                if nw in word_set and nw not in visited:
                    visited.add(nw)
                    q.append((nw, d + 1))
    return 0""",
    [
        (("hit", "cog", ["hot","dot","dog","lot","log","cog"]), 5),
        (("hit", "cog", ["hot","dot","dog","lot","log"]), 0),
    ],
    "public static int ladderLength(String beginWord, String endWord, List<String> wordList)",
    """        Set<String> wordSet = new HashSet<>(wordList);
        if (!wordSet.contains(endWord)) return 0;
        Deque<String> q = new ArrayDeque<>();
        q.offer(beginWord);
        Set<String> visited = new HashSet<>();
        visited.add(beginWord);
        int depth = 1;
        int L = beginWord.length();
        while (!q.isEmpty()) {
            int size = q.size();
            for (int i = 0; i < size; i++) {
                String word = q.poll();
                if (word.equals(endWord)) return depth;
                char[] arr = word.toCharArray();
                for (int j = 0; j < L; j++) {
                    char orig = arr[j];
                    for (char c = 'a'; c <= 'z'; c++) {
                        if (c == orig) continue;
                        arr[j] = c;
                        String nw = new String(arr);
                        if (wordSet.contains(nw) && !visited.contains(nw)) {
                            visited.add(nw);
                            q.offer(nw);
                        }
                    }
                    arr[j] = orig;
                }
            }
            depth++;
        }
        return 0;""",
    [],
    """BFS from `beginWord`. At each word, try all single-letter
substitutions. The first time we reach `endWord`, the BFS depth is the
answer.

**Time:** O(L · 26 · N) where L is the word length and N is the number
of words. **Space:** O(N) for the queue + visited.
""",
)
