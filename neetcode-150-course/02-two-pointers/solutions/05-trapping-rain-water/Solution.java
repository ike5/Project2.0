/** Trapping Rain Water.
 *
 *  02 Two Pointers - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-trapping-rain-water/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int trap(int[] height) {
            int l = 0, r = height.length - 1;
            int lMax = 0, rMax = 0, water = 0;
            while (l < r) {
                if (height[l] < height[r]) {
                    if (height[l] >= lMax) lMax = height[l];
                    else water += lMax - height[l];
                    l++;
                } else {
                    if (height[r] >= rMax) rMax = height[r];
                    else water += rMax - height[r];
                    r--;
                }
            }
            return water;
    }

    public static void main(String[] args) {
        System.out.println("1: " + trap(new int[]{0,1,0,2,1,0,1,3,2,1,2,1}));
        System.out.println("2: " + trap(new int[]{4,2,0,3,2,5}));
        System.out.println("3: " + trap(new int[]{1,0,1}));
    }
}
