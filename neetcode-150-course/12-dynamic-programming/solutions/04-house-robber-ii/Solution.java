/** House Robber II.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-house-robber-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int robCircle(int[] nums) {
            if (nums.length == 1) return nums[0];
            return Math.max(rob(nums, 0, nums.length - 1), rob(nums, 1, nums.length));
    }

    private static int rob(int[] nums, int lo, int hi) {
        if (lo + 1 >= hi) return nums[lo];
        int a = nums[lo], b = Math.max(nums[lo], nums[lo + 1]);
        for (int i = lo + 2; i < hi; i++) {
            int tmp = b;
            b = Math.max(b, a + nums[i]);
            a = tmp;
        }
        return b;
    }

    public static void main(String[] args) {
        System.out.println("1: " + robCircle(new int[]{2,3,2}));
        System.out.println("2: " + robCircle(new int[]{1,2,3,1}));
        System.out.println("3: " + robCircle(new int[]{0}));
    }
}
