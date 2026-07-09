/** Search a 2D Matrix.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-search-a-2d-matrix/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean searchMatrix(int[][] matrix, int target) {
            if (matrix.length == 0 || matrix[0].length == 0) return false;
            int m = matrix.length, n = matrix[0].length;
            int lo = 0, hi = m * n - 1;
            while (lo <= hi) {
                int mid = lo + (hi - lo) / 2;
                int v = matrix[mid / n][mid % n];
                if (v == target) return true;
                if (v < target) lo = mid + 1;
                else hi = mid - 1;
            }
            return false;
    }

    public static void main(String[] args) {
        System.out.println("searchMatrix ready");
    }
}
