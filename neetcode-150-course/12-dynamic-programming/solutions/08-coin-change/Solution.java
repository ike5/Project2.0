/** Coin Change.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/08-coin-change/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int coinChange(int[] coins, int amount) {
            int[] dp = new int[amount + 1];
            Arrays.fill(dp, amount + 1);
            dp[0] = 0;
            for (int c : coins) {
                for (int a = c; a <= amount; a++) {
                    if (dp[a - c] + 1 < dp[a]) dp[a] = dp[a - c] + 1;
                }
            }
            return dp[amount] == amount + 1 ? -1 : dp[amount];
    }

    public static void main(String[] args) {
        System.out.println("1: " + coinChange(new int[]{1,5,10,25}, 30));
        System.out.println("2: " + coinChange(new int[]{2}, 3));
    }
}
