/** Find Minimum in Rotated Sorted Array.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-find-minimum-in-rotated-sorted-array/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int findMin(int[] nums) {
            int lo = 0, hi = nums.length - 1;
            while (lo < hi) {
                int mid = lo + (hi - lo) / 2;
                if (nums[mid] > nums[hi]) lo = mid + 1;
                else hi = mid;
            }
            return nums[lo];
    }

    public static void main(String[] args) {
        System.out.println("1: " + findMin(new int[]{3,4,5,1,2}));
        System.out.println("2: " + findMin(new int[]{4,5,6,7,0,1,2}));
    }
}
