/** Graph Valid Tree.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/10-graph-valid-tree/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean validTree(int n, int[][] edges) {
            if (edges.length != n - 1) return false;
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
        return x;
    }

    public static void main(String[] args) {
        System.out.println("validTree ready");
    }
}
