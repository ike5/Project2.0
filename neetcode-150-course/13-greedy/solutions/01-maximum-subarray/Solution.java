/** Maximum Subarray.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-maximum-subarray/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxSubarray(int[] nums) {
            int best = nums[0], cur = nums[0];
            for (int i = 1; i < nums.length; i++) {
                cur = Math.max(nums[i], cur + nums[i]);
                best = Math.max(best, cur);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxSubarray(new int[]{-2,1,-3,4,-1,2,1,-5,4}));
        System.out.println("2: " + maxSubarray(new int[]{1}));
    }
}
