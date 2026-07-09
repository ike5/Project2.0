/** Rotting Oranges.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-rotting-oranges/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int orangesRotting(int[][] grid) {
            int rows = grid.length, cols = grid[0].length;
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
    }

    public static void main(String[] args) {
        System.out.println("orangesRotting ready");
    }
}
