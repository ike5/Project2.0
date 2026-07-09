/** Target Sum.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/17-target-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int findTargetSumWays(int[] nums, int target) {
            int total = 0;
            for (int x : nums) total += x;
            if (Math.abs(target) > total) return 0;
            if (((total + target) & 1) == 1) return 0;
            int p = (total + target) / 2;
            int[] dp = new int[p + 1];
            dp[0] = 1;
            for (int x : nums) {
                for (int s = p; s >= x; s--) {
                    dp[s] += dp[s - x];
                }
            }
            return dp[p];
    }

    public static void main(String[] args) {
        System.out.println("1: " + findTargetSumWays(new int[]{1,1,1,1,1}, 3));
        System.out.println("2: " + findTargetSumWays(new int[]{1}, 1));
    }
}
