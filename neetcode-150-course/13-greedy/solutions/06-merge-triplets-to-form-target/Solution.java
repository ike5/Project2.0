/** Merge Triplets to Form Target Triplet.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-merge-triplets-to-form-target/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean mergeTriplets(int[][] triplets, int[] target) {
            int[] cur = new int[3];
            for (int[] t : triplets) {
                if (t[0] <= target[0] && t[1] <= target[1] && t[2] <= target[2]) {
                    cur[0] = Math.max(cur[0], t[0]);
                    cur[1] = Math.max(cur[1], t[1]);
                    cur[2] = Math.max(cur[2], t[2]);
                }
            }
            return cur[0] == target[0] && cur[1] == target[1] && cur[2] == target[2];
    }

    public static void main(String[] args) {
        System.out.println("1: " + mergeTriplets(new int[][]{{2,5,3},{1,8,4},{1,7,5}}, new int[]{2,7,5}));
        System.out.println("2: " + mergeTriplets(new int[][]{{3,4,5},{4,5,6}}, new int[]{3,2,5}));
    }
}
