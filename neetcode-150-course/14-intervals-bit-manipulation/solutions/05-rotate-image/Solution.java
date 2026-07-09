/** Rotate Image.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-rotate-image/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[][] rotate(int[][] matrix) {
            int n = matrix.length;
            for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) {
                int tmp = matrix[i][j]; matrix[i][j] = matrix[j][i]; matrix[j][i] = tmp;
            }
            for (int[] row : matrix) {
                for (int l = 0, r = n - 1; l < r; l++, r--) {
                    int tmp = row[l]; row[l] = row[r]; row[r] = tmp;
                }
            }
            return matrix;
    }

    public static void main(String[] args) {
        System.out.println("rotate ready");
    }
}
