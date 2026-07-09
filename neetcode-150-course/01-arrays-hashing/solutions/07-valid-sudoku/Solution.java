/** Valid Sudoku.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-valid-sudoku/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean isValidSudoku(char[][] board) {
            Set<Character>[] rows = new Set[9];
            Set<Character>[] cols = new Set[9];
            Set<Character>[] boxes = new Set[9];
            for (int i = 0; i < 9; i++) {
                rows[i] = new HashSet<>();
                cols[i] = new HashSet<>();
                boxes[i] = new HashSet<>();
            }
            for (int r = 0; r < 9; r++) {
                for (int c = 0; c < 9; c++) {
                    char v = board[r][c];
                    if (v == '.') continue;
                    int b = (r / 3) * 3 + (c / 3);
                    if (!rows[r].add(v) || !cols[c].add(v) || !boxes[b].add(v)) {
                        return false;
                    }
                }
            }
            return true;
    }

    public static void main(String[] args) {
        System.out.println("isValidSudoku ready");
    }
}
