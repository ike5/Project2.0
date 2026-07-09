/** Redundant Connection.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/12-redundant-connection/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] findRedundantConnection(int[][] edges) {
            int n = edges.length;
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
        return x;
    }

    public static void main(String[] args) {
        System.out.println("findRedundantConnection ready");
    }
}
