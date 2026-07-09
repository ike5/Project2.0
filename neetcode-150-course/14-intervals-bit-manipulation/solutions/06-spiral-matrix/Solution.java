/** Spiral Matrix.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-spiral-matrix/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<Integer> spiralOrder(int[][] matrix) {
            List<Integer> out = new ArrayList<>();
            int top = 0, bottom = matrix.length - 1;
            int left = 0, right = matrix[0].length - 1;
            while (top <= bottom && left <= right) {
                for (int j = left; j <= right; j++) out.add(matrix[top][j]);
                top++;
                for (int i = top; i <= bottom; i++) out.add(matrix[i][right]);
                right--;
                if (top <= bottom) {
                    for (int j = right; j >= left; j--) out.add(matrix[bottom][j]);
                    bottom--;
                }
                if (left <= right) {
                    for (int i = bottom; i >= top; i--) out.add(matrix[i][left]);
                    left++;
                }
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("spiralOrder ready");
    }
}
