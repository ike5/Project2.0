/** Best Time to Buy and Sell Stock.
 *
 *  03 Sliding Window - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-best-time-to-buy-and-sell-stock/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxProfit(int[] prices) {
            int minPrice = Integer.MAX_VALUE;
            int best = 0;
            for (int p : prices) {
                if (p < minPrice) minPrice = p;
                else best = Math.max(best, p - minPrice);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxProfit(new int[]{7,1,5,3,6,4}));
        System.out.println("2: " + maxProfit(new int[]{7,6,4,3,1}));
    }
}
