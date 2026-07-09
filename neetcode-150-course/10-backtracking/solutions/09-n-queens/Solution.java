/** N-Queens.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/09-n-queens/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<String>> solveNQueens(int n) {
            Set<Integer> cols = new HashSet<>();
            Set<Integer> diag1 = new HashSet<>();   // r - c
            Set<Integer> diag2 = new HashSet<>();   // r + c
            char[][] board = new char[n][n];
            for (char[] row : board) Arrays.fill(row, '.');
            List<List<String>> out = new ArrayList<>();
            backtrack(out, board, cols, diag1, diag2, 0, n);
            return out;
    }

    private static void backtrack(List<List<String>> out, char[][] board, Set<Integer> cols, Set<Integer> diag1, Set<Integer> diag2, int r, int n) {
        if (r == n) {
            List<String> sol = new ArrayList<>();
            for (char[] row : board) sol.add(new String(row));
            out.add(sol);
            return;
        }
        for (int c = 0; c < n; c++) {
            if (cols.contains(c) || diag1.contains(r - c) || diag2.contains(r + c)) continue;
            board[r][c] = 'Q';
            cols.add(c); diag1.add(r - c); diag2.add(r + c);
            backtrack(out, board, cols, diag1, diag2, r + 1, n);
            board[r][c] = '.';
            cols.remove(c); diag1.remove(r - c); diag2.remove(r + c);
        }
    }

    public static void main(String[] args) {
        System.out.println("solveNQueens ready");
    }
}
