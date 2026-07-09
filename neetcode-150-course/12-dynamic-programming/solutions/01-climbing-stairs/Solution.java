/** Climbing Stairs.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-climbing-stairs/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int climbStairs(int n) {
            if (n <= 2) return n;
            int a = 1, b = 2;
            for (int i = 3; i <= n; i++) {
                int tmp = a + b;
                a = b;
                b = tmp;
            }
            return b;
    }

    public static void main(String[] args) {
        System.out.println("1: " + climbStairs(2));
        System.out.println("2: " + climbStairs(3));
        System.out.println("3: " + climbStairs(5));
    }
}
