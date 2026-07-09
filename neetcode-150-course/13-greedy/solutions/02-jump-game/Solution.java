/** Jump Game.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-jump-game/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean canJump(int[] nums) {
            int farthest = 0;
            for (int i = 0; i < nums.length; i++) {
                if (i > farthest) return false;
                farthest = Math.max(farthest, i + nums[i]);
            }
            return true;
    }

    public static void main(String[] args) {
        System.out.println("1: " + canJump(new int[]{2,3,1,1,4}));
        System.out.println("2: " + canJump(new int[]{3,2,1,0,4}));
    }
}
