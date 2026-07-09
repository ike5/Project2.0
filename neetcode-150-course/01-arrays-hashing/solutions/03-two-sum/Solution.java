/** Two Sum.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-two-sum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] twoSum(int[] nums, int target) {
            Map<Integer, Integer> seen = new HashMap<>();
            for (int i = 0; i < nums.length; i++) {
                int need = target - nums[i];
                if (seen.containsKey(need)) {
                    return new int[] { seen.get(need), i };
                }
                seen.put(nums[i], i);
            }
            return new int[] {};
    }

    public static void main(String[] args) {
        System.out.println("1: " + Arrays.toString(twoSum(new int[]{2, 7, 11, 15}, 9)));
        System.out.println("2: " + Arrays.toString(twoSum(new int[]{3, 2, 4}, 6)));
        System.out.println("3: " + Arrays.toString(twoSum(new int[]{3, 3}, 6)));
    }
}
