/** Best Time to Buy and Sell Stock IV.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/21-best-time-to-buy-and-sell-stock-iv/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxProfitK(int k, int[] prices) {
            int n = prices.length;
            if (k >= n / 2) {
                int s = 0;
                for (int i = 1; i < n; i++) if (prices[i] > prices[i - 1]) s += prices[i] - prices[i - 1];
                return s;
            }
            int[] buy = new int[k + 1];
            int[] sell = new int[k + 1];
            Arrays.fill(buy, Integer.MIN_VALUE);
            for (int p : prices) {
                for (int j = 1; j <= k; j++) {
                    buy[j] = Math.max(buy[j], sell[j - 1] - p);
                    sell[j] = Math.max(sell[j], buy[j] + p);
                }
            }
            return sell[k];
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxProfitK(2, new int[]{2,4,1}));
        System.out.println("2: " + maxProfitK(2, new int[]{3,2,6,5,0,3}));
    }
}
