/** Binary Tree Maximum Path Sum.
 *
 *  07 Trees - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/15-binary-tree-maximum-path-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static class TreeNode {
        int val;
        TreeNode left, right;
        TreeNode(int v) { val = v; }
        TreeNode(int v, TreeNode l, TreeNode r) { val = v; left = l; right = r; }
    }

    private static TreeNode fromArray(Integer[] arr) {
        if (arr == null || arr.length == 0 || arr[0] == null) return null;
        TreeNode[] nodes = new TreeNode[arr.length];
        for (int i = 0; i < arr.length; i++) {
            if (arr[i] != null) nodes[i] = new TreeNode(arr[i]);
        }
        java.util.List<TreeNode> kids = new java.util.ArrayList<>();
        for (int i = 1; i < arr.length; i++) kids.add(nodes[i]);
        for (TreeNode parent : nodes) {
            if (parent == null) continue;
            if (!kids.isEmpty()) parent.left = kids.remove(0);
            if (!kids.isEmpty()) parent.right = kids.remove(0);
        }
        return nodes[0];
    }

    private static Integer[] toArrayTree(TreeNode node) {
        if (node == null) return new Integer[0];
        java.util.List<Integer> out = new java.util.ArrayList<>();
        java.util.List<TreeNode> q = new java.util.ArrayList<>();
        q.add(node);
        while (!q.isEmpty()) {
            TreeNode n = q.remove(0);
            if (n == null) { out.add(null); continue; }
            out.add(n.val);
            q.add(n.left);
            q.add(n.right);
        }
        while (!out.isEmpty() && out.get(out.size() - 1) == null) out.remove(out.size() - 1);
        return out.toArray(new Integer[0]);
    }

    public static int maxPathSum(TreeNode root) {
            int[] best = { Integer.MIN_VALUE };
            gain(root, best);
            return best[0];
    }

    private static int gain(TreeNode node, int[] best) {
        if (node == null) return 0;
        int left = Math.max(0, gain(node.left, best));
        int right = Math.max(0, gain(node.right, best));
        best[0] = Math.max(best[0], node.val + left + right);
        return node.val + Math.max(left, right);
    }

    public static void main(String[] args) {
        System.out.println("maxPathSum ready");
    }
}
