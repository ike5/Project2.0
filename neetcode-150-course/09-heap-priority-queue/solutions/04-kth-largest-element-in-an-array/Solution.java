/** Kth Largest Element in an Array.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-kth-largest-element-in-an-array/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int kthLargest(int[] nums, int k) {
            PriorityQueue<Integer> heap = new PriorityQueue<>();
            for (int n : nums) {
                heap.offer(n);
                if (heap.size() > k) heap.poll();
            }
            return heap.peek();
    }

    public static void main(String[] args) {
        System.out.println("1: " + kthLargest(new int[]{3,2,1,5,6,4}, 2));
        System.out.println("2: " + kthLargest(new int[]{3,2,3,1,2,4,5,5,6}, 4));
    }
}
