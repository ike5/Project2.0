/** Longest Common Subsequence.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/14-longest-common-subsequence/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int longestCommonSubsequence(String text1, String text2) {
            int m = text1.length(), n = text2.length();
            int[] dp = new int[n + 1];
            for (int i = 1; i <= m; i++) {
                int prev = 0;
                for (int j = 1; j <= n; j++) {
                    int tmp = dp[j];
                    if (text1.charAt(i - 1) == text2.charAt(j - 1)) dp[j] = prev + 1;
                    else dp[j] = Math.max(dp[j], dp[j - 1]);
                    prev = tmp;
                }
            }
            return dp[n];
    }

    public static void main(String[] args) {
        System.out.println("1: " + longestCommonSubsequence("abcde", "ace"));
        System.out.println("2: " + longestCommonSubsequence("abc", "abc"));
    }
}
