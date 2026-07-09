/** Edit Distance.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/19-edit-distance/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int minDistance(String word1, String word2) {
            int m = word1.length(), n = word2.length();
            int[] dp = new int[n + 1];
            for (int j = 0; j <= n; j++) dp[j] = j;
            for (int i = 1; i <= m; i++) {
                int prev = dp[0];
                dp[0] = i;
                for (int j = 1; j <= n; j++) {
                    int tmp = dp[j];
                    if (word1.charAt(i - 1) == word2.charAt(j - 1)) dp[j] = prev;
                    else dp[j] = 1 + Math.min(Math.min(prev, dp[j]), dp[j - 1]);
                    prev = tmp;
                }
            }
            return dp[n];
    }

    public static void main(String[] args) {
        System.out.println("1: " + minDistance("horse", "ros"));
        System.out.println("2: " + minDistance("intention", "execution"));
    }
}
