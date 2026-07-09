/** Search in Rotated Sorted Array.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-search-in-rotated-sorted-array/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int searchRotated(int[] nums, int target) {
            int lo = 0, hi = nums.length - 1;
            while (lo <= hi) {
                int mid = lo + (hi - lo) / 2;
                if (nums[mid] == target) return mid;
                if (nums[lo] <= nums[mid]) {
                    if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                    else lo = mid + 1;
                } else {
                    if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                    else hi = mid - 1;
                }
            }
            return -1;
    }

    public static void main(String[] args) {
        System.out.println("1: " + searchRotated(new int[]{4,5,6,7,0,1,2}, 0));
        System.out.println("2: " + searchRotated(new int[]{4,5,6,7,0,1,2}, 3));
    }
}
