/** Largest Rectangle in Histogram.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-largest-rectangle-in-histogram/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int largestRectangleArea(int[] heights) {
            Deque<Integer> stack = new ArrayDeque<>();
            int best = 0;
            int n = heights.length;
            for (int i = 0; i <= n; i++) {
                int h = (i == n) ? 0 : heights[i];
                while (!stack.isEmpty() && heights[stack.peek()] >= h) {
                    int height = heights[stack.pop()];
                    int left = stack.isEmpty() ? -1 : stack.peek();
                    int width = i - left - 1;
                    best = Math.max(best, height * width);
                }
                stack.push(i);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + largestRectangleArea(new int[]{2,1,5,6,2,3}));
        System.out.println("2: " + largestRectangleArea(new int[]{2,4}));
    }
}
