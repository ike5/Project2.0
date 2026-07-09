/** Subsets.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-subsets/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> subsets(int[] nums) {
            List<List<Integer>> out = new ArrayList<>();
            backtrack(out, nums, 0, new ArrayList<>());
            return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] nums, int i, List<Integer> path) {
        if (i == nums.length) { out.add(new ArrayList<>(path)); return; }
        // skip nums[i]
        backtrack(out, nums, i + 1, path);
        // include nums[i]
        path.add(nums[i]);
        backtrack(out, nums, i + 1, path);
        path.remove(path.size() - 1);
    }

    public static void main(String[] args) {
        System.out.println("subsets ready");
    }
}
