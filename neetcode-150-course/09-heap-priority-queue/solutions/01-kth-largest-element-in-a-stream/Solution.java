/** Kth Largest Element in a Stream.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-kth-largest-element-in-a-stream/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static class KthLargest {
        private final int k;
        private final PriorityQueue<Integer> heap = new PriorityQueue<>();
        public KthLargest(int k, int[] nums) {
            this.k = k;
            for (int n : nums) add(n);
        }
        public int add(int val) {
            heap.offer(val);
            if (heap.size() > k) heap.poll();
            return heap.peek();
        }
    }

    public static void main(String[] args) {
        System.out.println("add ready");
    }
}
