/** Binary Tree Right Side View.
 *
 *  07 Trees - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/11-binary-tree-right-side-view/Solution.java
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

    public static List<Integer> rightSideView(TreeNode root) {
            List<Integer> out = new ArrayList<>();
            if (root == null) return out;
            Deque<TreeNode> q = new ArrayDeque<>();
            q.offer(root);
            while (!q.isEmpty()) {
                int size = q.size();
                for (int i = 0; i < size; i++) {
                    TreeNode n = q.poll();
                    if (i == size - 1) out.add(n.val);
                    if (n.left != null) q.offer(n.left);
                    if (n.right != null) q.offer(n.right);
                }
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("rightSideView ready");
    }
}
