/** Longest Consecutive Sequence.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/09-longest-consecutive-sequence/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int longestConsecutive(int[] nums) {
            Set<Integer> s = new HashSet<>();
            for (int x : nums) s.add(x);
            int best = 0;
            for (int x : s) {
                if (s.contains(x - 1)) continue;
                int length = 1;
                while (s.contains(x + length)) length++;
                best = Math.max(best, length);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + longestConsecutive(new int[]{100,4,200,1,3,2}));
        System.out.println("2: " + longestConsecutive(new int[]{0,3,7,2,5,8,4,6,0,1}));
        System.out.println("3: " + longestConsecutive(new int[]{}));
    }
}
