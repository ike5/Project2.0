/** Permutations.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-permutations/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> permute(int[] nums) {
            List<List<Integer>> out = new ArrayList<>();
            backtrack(out, nums, new ArrayList<>(), new boolean[nums.length]);
            return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] nums, List<Integer> path, boolean[] used) {
        if (path.size() == nums.length) { out.add(new ArrayList<>(path)); return; }
        for (int i = 0; i < nums.length; i++) {
            if (used[i]) continue;
            used[i] = true;
            path.add(nums[i]);
            backtrack(out, nums, path, used);
            path.remove(path.size() - 1);
            used[i] = false;
        }
    }

    public static void main(String[] args) {
        System.out.println("permute ready");
    }
}
