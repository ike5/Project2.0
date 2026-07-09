/** Coin Change II.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/16-coin-change-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int change(int amount, int[] coins) {
            int[] dp = new int[amount + 1];
            dp[0] = 1;
            for (int c : coins) {
                for (int a = c; a <= amount; a++) {
                    dp[a] += dp[a - c];
                }
            }
            return dp[amount];
    }

    public static void main(String[] args) {
        System.out.println("1: " + change(5, new int[]{1,2,5}));
        System.out.println("2: " + change(3, new int[]{2}));
    }
}
