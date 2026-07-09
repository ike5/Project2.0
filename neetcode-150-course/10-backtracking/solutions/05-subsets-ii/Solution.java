/** Subsets II.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-subsets-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> subsetsWithDup(int[] nums) {
            Arrays.sort(nums);
            List<List<Integer>> out = new ArrayList<>();
            backtrack(out, nums, 0, new ArrayList<>());
            return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] nums, int i, List<Integer> path) {
        out.add(new ArrayList<>(path));
        for (int j = i; j < nums.length; j++) {
            if (j > i && nums[j] == nums[j - 1]) continue;
            path.add(nums[j]);
            backtrack(out, nums, j + 1, path);
            path.remove(path.size() - 1);
        }
    }

    public static void main(String[] args) {
        System.out.println("subsetsWithDup ready");
    }
}
