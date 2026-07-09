/** Binary Search.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-binary-search/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int search(int[] nums, int target) {
            int lo = 0, hi = nums.length - 1;
            while (lo <= hi) {
                int mid = lo + (hi - lo) / 2;
                if (nums[mid] == target) return mid;
                if (nums[mid] < target) lo = mid + 1;
                else hi = mid - 1;
            }
            return -1;
    }

    public static void main(String[] args) {
        System.out.println("1: " + search(new int[]{-1,0,3,5,9,12}, 9));
        System.out.println("2: " + search(new int[]{-1,0,3,5,9,12}, 2));
    }
}
