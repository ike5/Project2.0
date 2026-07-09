/** Container With Most Water.
 *
 *  02 Two Pointers - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-container-with-most-water/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int maxArea(int[] height) {
            int l = 0, r = height.length - 1;
            int best = 0;
            while (l < r) {
                int area = (r - l) * Math.min(height[l], height[r]);
                best = Math.max(best, area);
                if (height[l] < height[r]) l++;
                else r--;
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + maxArea(new int[]{1,8,6,2,5,4,8,3,7}));
        System.out.println("2: " + maxArea(new int[]{1,1}));
        System.out.println("3: " + maxArea(new int[]{4,3,2,1,4}));
    }
}
