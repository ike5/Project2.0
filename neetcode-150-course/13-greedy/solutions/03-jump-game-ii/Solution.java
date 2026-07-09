/** Jump Game II.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-jump-game-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int jump(int[] nums) {
            int jumps = 0, curEnd = 0, farthest = 0;
            for (int i = 0; i < nums.length - 1; i++) {
                farthest = Math.max(farthest, i + nums[i]);
                if (i == curEnd) { jumps++; curEnd = farthest; }
            }
            return jumps;
    }

    public static void main(String[] args) {
        System.out.println("1: " + jump(new int[]{2,3,1,1,4}));
        System.out.println("2: " + jump(new int[]{2,3,0,1,4}));
    }
}
