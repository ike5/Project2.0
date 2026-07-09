/** Two Sum II — Input Array Is Sorted.
 *
 *  02 Two Pointers - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-two-sum-ii-input-array-is-sorted/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] twoSumSorted(int[] numbers, int target) {
            int l = 0, r = numbers.length - 1;
            while (l < r) {
                int s = numbers[l] + numbers[r];
                if (s == target) return new int[] { l + 1, r + 1 };
                if (s < target) l++;
                else r--;
            }
            return new int[] {};
    }

    public static void main(String[] args) {
        System.out.println("1: " + Arrays.toString(twoSumSorted(new int[]{2,7,11,15}, 9)));
        System.out.println("2: " + Arrays.toString(twoSumSorted(new int[]{2,3,4}, 6)));
        System.out.println("3: " + Arrays.toString(twoSumSorted(new int[]{-1,0}, -1)));
    }
}
