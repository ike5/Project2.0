/** Word Search.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-word-search/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean exist(char[][] board, String word) {
            int rows = board.length, cols = board[0].length;
            for (int r = 0; r < rows; r++) {
                for (int c = 0; c < cols; c++) {
                    if (dfs(board, r, c, 0, word)) return true;
                }
            }
            return false;
    }

    private static boolean dfs(char[][] board, int r, int c, int i, String word) {
        if (i == word.length()) return true;
        if (r < 0 || c < 0 || r >= board.length || c >= board[0].length || board[r][c] != word.charAt(i)) return false;
        char saved = board[r][c];
        board[r][c] = '#';
        boolean found = dfs(board, r + 1, c, i + 1, word)
                     || dfs(board, r - 1, c, i + 1, word)
                     || dfs(board, r, c + 1, i + 1, word)
                     || dfs(board, r, c - 1, i + 1, word);
        board[r][c] = saved;
        return found;
    }

    public static void main(String[] args) {
        System.out.println("exist ready");
    }
}
