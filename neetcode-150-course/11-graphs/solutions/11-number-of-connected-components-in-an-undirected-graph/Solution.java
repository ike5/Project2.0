/** Number of Connected Components in an Undirected Graph.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/11-number-of-connected-components-in-an-undirected-graph/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int countComponents(int n, int[][] edges) {
            int[] parent = new int[n];
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
        return x;
    }

    public static void main(String[] args) {
        System.out.println("countComponents ready");
    }
}
