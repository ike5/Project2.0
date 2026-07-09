/** Best Time to Buy and Sell Stock III.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/20-best-time-to-buy-and-sell-stock-iii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxProfitTwo(int[] prices) {
            int buy1 = -prices[0], sell1 = 0;
            int buy2 = -prices[0], sell2 = 0;
            for (int i = 1; i < prices.length; i++) {
                int p = prices[i];
                buy1 = Math.max(buy1, -p);
                sell1 = Math.max(sell1, buy1 + p);
                buy2 = Math.max(buy2, sell1 - p);
                sell2 = Math.max(sell2, buy2 + p);
            }
            return sell2;
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxProfitTwo(new int[]{3,3,5,0,0,3,1,4}));
        System.out.println("2: " + maxProfitTwo(new int[]{1,2,3,4,5}));
    }
}
