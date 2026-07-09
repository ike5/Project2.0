/** Pacific Atlantic Water Flow.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-pacific-atlantic-water-flow/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> pacificAtlantic(int[][] heights) {
            int rows = heights.length, cols = heights[0].length;
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
    }

    public static void main(String[] args) {
        System.out.println("pacificAtlantic ready");
    }
}
