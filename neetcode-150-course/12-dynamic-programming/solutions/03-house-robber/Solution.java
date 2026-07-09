/** House Robber.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-house-robber/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int rob(int[] nums) {
            if (nums.length == 0) return 0;
            if (nums.length == 1) return nums[0];
            int a = nums[0], b = Math.max(nums[0], nums[1]);
            for (int i = 2; i < nums.length; i++) {
                int tmp = b;
                b = Math.max(b, a + nums[i]);
                a = tmp;
            }
            return b;
    }

    public static void main(String[] args) {
        System.out.println("1: " + rob(new int[]{1,2,3,1}));
        System.out.println("2: " + rob(new int[]{2,7,9,3,1}));
    }
}
