/** Find the Duplicate Number.
 *
 *  06 Linked List - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/08-find-the-duplicate-number/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int findDuplicate(int[] nums) {
            int slow = nums[0], fast = nums[0];
            while (true) {
                slow = nums[slow];
                fast = nums[nums[fast]];
                if (slow == fast) break;
            }
            int finder = nums[0];
            while (finder != slow) {
                finder = nums[finder];
                slow = nums[slow];
            }
            return finder;
    }

    public static void main(String[] args) {
        System.out.println("1: " + findDuplicate(new int[]{1,3,4,2,2}));
        System.out.println("2: " + findDuplicate(new int[]{3,1,3,4,2}));
    }
}
