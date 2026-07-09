/** Partition Equal Subset Sum.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/12-partition-equal-subset-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean canPartition(int[] nums) {
            int total = 0;
            for (int x : nums) total += x;
            if ((total & 1) == 1) return false;
            int target = total / 2;
            boolean[] dp = new boolean[target + 1];
            dp[0] = true;
            for (int x : nums) {
                for (int s = target; s >= x; s--) {
                    if (dp[s - x]) dp[s] = true;
                }
            }
            return dp[target];
    }

    public static void main(String[] args) {
        System.out.println("1: " + canPartition(new int[]{1,5,11,5}));
        System.out.println("2: " + canPartition(new int[]{1,2,3,5}));
    }
}
