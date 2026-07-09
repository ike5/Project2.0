/** Min Cost Climbing Stairs.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-min-cost-climbing-stairs/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int minCostClimbingStairs(int[] cost) {
            int a = cost[0], b = cost[1];
            for (int i = 2; i < cost.length; i++) {
                int tmp = b;
                b = cost[i] + Math.min(a, b);
                a = tmp;
            }
            return Math.min(a, b);
    }

    public static void main(String[] args) {
        System.out.println("1: " + minCostClimbingStairs(new int[]{10,15,20}));
        System.out.println("2: " + minCostClimbingStairs(new int[]{1,100,1,1,1,100,1,1,100,1}));
    }
}
