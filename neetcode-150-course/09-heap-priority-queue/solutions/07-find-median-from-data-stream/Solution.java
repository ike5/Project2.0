/** Find Median from Data Stream.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-find-median-from-data-stream/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

        private final PriorityQueue<Integer> small = new PriorityQueue<>(Comparator.reverseOrder());
        private final PriorityQueue<Integer> large = new PriorityQueue<>();
        public void addNum(int num) {
            small.offer(num);
            if (!large.isEmpty() && small.peek() > large.peek()) {
                large.offer(small.poll());
            }
            if (small.size() > large.size() + 1) {
                large.offer(small.poll());
            } else if (large.size() > small.size()) {
                small.offer(large.poll());
            }
        }
        public double findMedian() {
            if (small.size() > large.size()) return small.peek();
            return (small.peek() + large.peek()) / 2.0;
        }

    public static void main(String[] args) {
        System.out.println("MedianFinder ready");
    }
}
