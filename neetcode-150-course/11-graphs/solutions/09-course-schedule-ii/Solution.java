/** Course Schedule II.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/09-course-schedule-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] findOrder(int numCourses, int[][] prerequisites) {
            List<List<Integer>> g = new ArrayList<>();
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
            return idx == numCourses ? order : new int[0];
    }

    public static void main(String[] args) {
        System.out.println("findOrder ready");
    }
}
