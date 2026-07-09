/** Minimum Size Subarray Sum.
 *
 *  03 Sliding Window - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-minimum-size-subarray-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int minSubArrayLen(int target, int[] nums) {
            int l = 0, s = 0, best = Integer.MAX_VALUE;
            for (int r = 0; r < nums.length; r++) {
                s += nums[r];
                while (s >= target) {
                    best = Math.min(best, r - l + 1);
                    s -= nums[l];
                    l++;
                }
            }
            return best == Integer.MAX_VALUE ? 0 : best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + minSubArrayLen(7, new int[]{2,3,1,2,4,3}));
        System.out.println("2: " + minSubArrayLen(4, new int[]{1,4,4}));
        System.out.println("3: " + minSubArrayLen(11, new int[]{1,1,1,1,1,1,1,1}));
    }
}
