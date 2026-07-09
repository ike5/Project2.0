/** Maximal Square.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/22-maximal-square/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maximalSquare(char[][] matrix) {
            int m = matrix.length, n = matrix[0].length;
            int[] dp = new int[n + 1];
            int best = 0;
            for (int i = 1; i <= m; i++) {
                int prev = 0;
                for (int j = 1; j <= n; j++) {
                    int tmp = dp[j];
                    if (matrix[i - 1][j - 1] == '1') {
                        dp[j] = 1 + Math.min(Math.min(prev, dp[j]), dp[j - 1]);
                        best = Math.max(best, dp[j]);
                    } else dp[j] = 0;
                    prev = tmp;
                }
            }
            return best * best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + maximalSquare(new char[][]{{'1','0','1','0','0'},{'1','0','1','1','1'},{'1','1','1','1','1'},{'1','0','0','1','0'}}));
    }
}
