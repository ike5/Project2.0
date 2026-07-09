/** Clone Graph.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-clone-graph/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static class GraphNode {
        int val;
        java.util.List<GraphNode> neighbors = new java.util.ArrayList<>();
        GraphNode(int v) { val = v; }
    }

    public static int cloneGraph(int[][] adj) {
            if (adj == null || adj.length == 0) return 0;
            GraphNode[] nodes = new GraphNode[adj.length + 1];
            for (int i = 1; i <= adj.length; i++) nodes[i] = new GraphNode(i);
            for (int i = 1; i <= adj.length; i++) {
                for (int j : adj[i - 1]) nodes[i].neighbors.add(nodes[j]);
            }
            Map<Integer, GraphNode> cloned = new HashMap<>();
            dfs(nodes[1], cloned);
            return cloned.size();
    }

    private static GraphNode dfs(GraphNode n, Map<Integer, GraphNode> cloned) {
        if (cloned.containsKey(n.val)) return cloned.get(n.val);
        GraphNode copy = new GraphNode(n.val);
        cloned.put(n.val, copy);
        copy.neighbors = new ArrayList<>();
        for (GraphNode nb : n.neighbors) copy.neighbors.add(dfs(nb, cloned));
        return copy;
    }

    public static void main(String[] args) {
        System.out.println("cloneGraph ready");
    }
}
