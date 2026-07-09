# Lab 11 — Graphs

**You'll:** implement *Number of Islands* and *Course Schedule* in both
languages. ⏱️ ~1.5 h.

---

## Part A — *Number of Islands* in Python

```python
def num_islands(grid):
    if not grid: return 0
    # your code
    ...


if __name__ == "__main__":
    g1 = [
        ["1","1","1","1","0"],
        ["1","1","0","1","0"],
        ["1","1","0","0","0"],
        ["0","0","0","0","0"]
    ]
    assert num_islands(g1) == 1
    g2 = [
        ["1","1","0","0","0"],
        ["1","1","0","0","0"],
        ["0","0","1","0","0"],
        ["0","0","0","1","1"]
    ]
    assert num_islands(g2) == 3
    print("all tests passed")
```

**Walk-through:** DFS on the grid, marking visited cells.

```python
def num_islands(grid):
    if not grid: return 0
    rows, cols = len(grid), len(grid[0])

    def dfs(r, c):
        if r < 0 or c < 0 or r >= rows or c >= cols or grid[r][c] != '1':
            return
        grid[r][c] = '#'
        dfs(r + 1, c); dfs(r - 1, c)
        dfs(r, c + 1); dfs(r, c - 1)

    count = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == '1':
                count += 1
                dfs(r, c)
    return count
```

## Part B — *Number of Islands* in Java 21

```java
public class LabIslands {
    public static int numIslands(char[][] grid) {
        // your code
    }

    public static void main(String[] args) {
        char[][] g1 = {
            {'1','1','1','1','0'},
            {'1','1','0','1','0'},
            {'1','1','0','0','0'},
            {'0','0','0','0','0'}
        };
        assert numIslands(g1) == 1;
        char[][] g2 = {
            {'1','1','0','0','0'},
            {'1','1','0','0','0'},
            {'0','0','1','0','0'},
            {'0','0','0','1','1'}
        };
        assert numIslands(g2) == 3;
        System.out.println("all tests passed");
    }
}
```

## Part C — *Course Schedule* in Python

```python
def can_finish(num_courses, prerequisites):
    # your code
    ...


if __name__ == "__main__":
    assert can_finish(2, [[1, 0]]) is True
    assert can_finish(2, [[1, 0], [0, 1]]) is False
    assert can_finish(3, [[1, 0], [2, 1]]) is True
    print("all tests passed")
```

**Walk-through:** Kahn's algorithm.

```python
def can_finish(num_courses, prerequisites):
    from collections import defaultdict, deque
    g = defaultdict(list)
    indeg = [0] * num_courses
    for a, b in prerequisites:
        g[b].append(a)
        indeg[a] += 1
    q = deque(i for i in range(num_courses) if indeg[i] == 0)
    taken = 0
    while q:
        c = q.popleft()
        taken += 1
        for nb in g[c]:
            indeg[nb] -= 1
            if indeg[nb] == 0:
                q.append(nb)
    return taken == num_courses
```

## Part D — *Course Schedule* in Java 21

```java
import java.util.*;

public class LabCourseSchedule {
    public static boolean canFinish(int numCourses, int[][] prerequisites) {
        // your code
    }

    public static void main(String[] args) {
        assert canFinish(2, new int[][]{{1, 0}});
        assert !canFinish(2, new int[][]{{1, 0}, {0, 1}});
        assert canFinish(3, new int[][]{{1, 0}, {2, 1}});
        System.out.println("all tests passed");
    }
}
```

## What you learned

- **Grid DFS** with the "mark and recurse" idiom. Mark visited cells
  with `'#'` to avoid revisiting.
- **Kahn's algorithm** for cycle detection: if we can't take all courses,
  there's a cycle.

➡️ **[challenge.md](./challenge.md)**
