/** Maximum Product Subarray.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/09-maximum-product-subarray/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxProduct(int[] nums) {
            int best = nums[0], maxEnd = nums[0], minEnd = nums[0];
            for (int i = 1; i < nums.length; i++) {
                int x = nums[i];
                if (x < 0) { int t = maxEnd; maxEnd = minEnd; minEnd = t; }
                maxEnd = Math.max(x, maxEnd * x);
                minEnd = Math.min(x, minEnd * x);
                best = Math.max(best, maxEnd);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxProduct(new int[]{2,3,-2,4}));
        System.out.println("2: " + maxProduct(new int[]{-2,0,-1}));
    }
}
