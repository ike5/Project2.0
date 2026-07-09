/** Combination Sum.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-combination-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<Integer>> combinationSum(int[] candidates, int target) {
            List<List<Integer>> out = new ArrayList<>();
            backtrack(out, candidates, 0, new ArrayList<>(), 0, target);
            return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] candidates, int i, List<Integer> path, int total, int target) {
        if (total == target) { out.add(new ArrayList<>(path)); return; }
        if (total > target || i == candidates.length) return;
        backtrack(out, candidates, i + 1, path, total, target);
        path.add(candidates[i]);
        backtrack(out, candidates, i, path, total + candidates[i], target);
        path.remove(path.size() - 1);
    }

    public static void main(String[] args) {
        System.out.println("combinationSum ready");
    }
}
