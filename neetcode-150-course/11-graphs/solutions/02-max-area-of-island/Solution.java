/** Max Area of Island.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-max-area-of-island/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxAreaOfIsland(int[][] grid) {
            int rows = grid.length, cols = grid[0].length;
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
        return 1 + dfs(grid, r + 1, c) + dfs(grid, r - 1, c) + dfs(grid, r, c + 1) + dfs(grid, r, c - 1);
    }

    public static void main(String[] args) {
        System.out.println("maxAreaOfIsland ready");
    }
}
