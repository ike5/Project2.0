/** Combination Sum II.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-combination-sum-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> combinationSum2(int[] candidates, int target) {
            Arrays.sort(candidates);
            List<List<Integer>> out = new ArrayList<>();
            backtrack(out, candidates, 0, new ArrayList<>(), 0, target);
            return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] candidates, int i, List<Integer> path, int total, int target) {
        if (total == target) { out.add(new ArrayList<>(path)); return; }
        if (total > target) return;
        int prev = Integer.MIN_VALUE;
        for (int j = i; j < candidates.length; j++) {
            if (candidates[j] == prev) continue;
            if (total + candidates[j] > target) break;
            path.add(candidates[j]);
            backtrack(out, candidates, j + 1, path, total + candidates[j], target);
            path.remove(path.size() - 1);
            prev = candidates[j];
        }
    }

    public static void main(String[] args) {
        System.out.println("combinationSum2 ready");
    }
}
