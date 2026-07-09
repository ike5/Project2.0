/** Unique Paths.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/13-unique-paths/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int uniquePaths(int m, int n) {
            int[] row = new int[n];
            Arrays.fill(row, 1);
            for (int i = 1; i < m; i++) {
                for (int j = 1; j < n; j++) {
                    row[j] += row[j - 1];
                }
            }
            return row[n - 1];
    }

    public static void main(String[] args) {
        System.out.println("1: " + uniquePaths(3, 7));
        System.out.println("2: " + uniquePaths(3, 2));
    }
}
