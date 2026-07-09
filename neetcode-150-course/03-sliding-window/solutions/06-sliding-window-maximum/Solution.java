/** Sliding Window Maximum.
 *
 *  03 Sliding Window - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-sliding-window-maximum/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] maxSlidingWindow(int[] nums, int k) {
            Deque<Integer> q = new ArrayDeque<>();
            int n = nums.length;
            int[] out = new int[n - k + 1];
            int idx = 0;
            for (int i = 0; i < n; i++) {
                while (!q.isEmpty() && nums[q.peekLast()] <= nums[i]) q.pollLast();
                q.offerLast(i);
                if (q.peekFirst() <= i - k) q.pollFirst();
                if (i >= k - 1) out[idx++] = nums[q.peekFirst()];
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("1: " + Arrays.toString(maxSlidingWindow(new int[]{1,3,-1,-3,5,3,6,7}, 3)));
        System.out.println("2: " + Arrays.toString(maxSlidingWindow(new int[]{1}, 1)));
    }
}
