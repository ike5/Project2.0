/** Best Time to Buy and Sell Stock with Cooldown.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/15-best-time-to-buy-and-sell-stock-with-cooldown/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxProfitCooldown(int[] prices) {
            int n = prices.length;
            if (n < 2) return 0;
            int free = 0, hold = -prices[0], sold = 0;
            for (int i = 1; i < n; i++) {
                int newFree = Math.max(free, sold);
                int newSold = hold + prices[i];
                int newHold = Math.max(hold, free - prices[i]);
                free = newFree; sold = newSold; hold = newHold;
            }
            return Math.max(free, sold);
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxProfitCooldown(new int[]{1,2,3,0,2}));
        System.out.println("2: " + maxProfitCooldown(new int[]{1}));
    }
}
