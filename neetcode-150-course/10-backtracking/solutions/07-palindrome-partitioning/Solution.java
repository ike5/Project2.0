/** Palindrome Partitioning.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-palindrome-partitioning/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<String>> partition(String s) {
            int n = s.length();
            boolean[][] isPal = new boolean[n][n];
            for (int i = n - 1; i >= 0; i--) {
                for (int j = i; j < n; j++) {
                    if (s.charAt(i) == s.charAt(j) && (j - i < 2 || isPal[i + 1][j - 1])) {
                        isPal[i][j] = true;
                    }
                }
            }
            List<List<String>> out = new ArrayList<>();
            backtrack(out, isPal, s, 0, new ArrayList<>());
            return out;
    }

    private static void backtrack(List<List<String>> out, boolean[][] isPal, String s, int i, List<String> path) {
        if (i == s.length()) { out.add(new ArrayList<>(path)); return; }
        for (int j = i; j < s.length(); j++) {
            if (!isPal[i][j]) continue;
            path.add(s.substring(i, j + 1));
            backtrack(out, isPal, s, j + 1, path);
            path.remove(path.size() - 1);
        }
    }

    public static void main(String[] args) {
        System.out.println("partition ready");
    }
}
