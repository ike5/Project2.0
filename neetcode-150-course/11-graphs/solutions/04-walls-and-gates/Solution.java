/** Walls and Gates.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-walls-and-gates/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static void wallsAndGates(int[][] rooms) {
            int rows = rooms.length, cols = rooms[0].length;
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
            }
    }

    public static void main(String[] args) {
        System.out.println("wallsAndGates ready");
    }
}
