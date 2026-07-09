# Pacific Atlantic Water Flow - walkthrough

**Difficulty:** Medium &middot; **Module:** 11 Graphs

## Brief

There is an `m x n` rectangular island that borders both the **Pacific Ocean** and the **Atlantic Ocean**. The Pacific Ocean touches the island's left and top edges, and the Atlantic Ocean touches the island's right and bottom edges. The island is partitioned into a grid of square cells. You are given an `m x n` integer matrix `heights` where `heights[r][c]` represents the height above sea level of the cell at coordinates `(r, c)`. The island receives a lot of rain, and the rain water can flow to neighboring cells directly north, south, east, and west if the neighboring cell's height is less than or equal to the current cell's height. Water can flow from any cell adjacent to an ocean into that ocean. Return a 2D list of grid coordinates `result` where `result[i] = [ri, ci]` denotes that rain water can flow from cell `(ri, ci)` to **both** the Pacific and Atlantic oceans.

## Examples

- `heights = [[1,2,2,3,5],[3,2,3,4,4],[2,4,5,3,1],[6,7,1,4,5],[5,1,1,2,4]]` &rarr; `[[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]`

## Constraints

- m == heights.length, n == heights[i].length
- 1 <= m, n <= 200
- 0 <= heights[r][c] <= 10^5

## Intuition

**Reverse the problem.** BFS from the Pacific (top + left edges)
inward, marking all cells that can flow to it. Do the same for
Atlantic (bottom + right). The intersection is the answer.

**Time:** O(m·n). **Space:** O(m·n).

## Reference solutions

- [`solution.py`](./solution.py) - Python 3.10+
- [`Solution.java`](./Solution.java) - Java 21
