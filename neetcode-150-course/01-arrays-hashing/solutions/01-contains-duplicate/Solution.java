/** Contains Duplicate.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-contains-duplicate/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean containsDuplicate(int[] nums) {
            Set<Integer> seen = new HashSet<>();
            for (int x : nums) {
                if (!seen.add(x)) return true;
            }
            return false;
    }

    public static void main(String[] args) {
        System.out.println("1: " + containsDuplicate(new int[]{1, 2, 3, 1}));
        System.out.println("2: " + containsDuplicate(new int[]{1, 2, 3, 4}));
        System.out.println("3: " + containsDuplicate(new int[]{1, 1, 1, 3, 3, 4, 3, 2, 4, 2}));
        System.out.println("4: " + containsDuplicate(new int[]{}));
    }
}
