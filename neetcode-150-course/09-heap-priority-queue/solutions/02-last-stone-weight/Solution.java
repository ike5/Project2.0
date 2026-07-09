/** Last Stone Weight.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-last-stone-weight/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int lastStoneWeight(int[] stones) {
            PriorityQueue<Integer> heap = new PriorityQueue<>(Comparator.reverseOrder());
            for (int s : stones) heap.offer(s);
            while (heap.size() > 1) {
                int a = heap.poll(), b = heap.poll();
                if (a != b) heap.offer(a - b);
            }
            return heap.isEmpty() ? 0 : heap.poll();
    }

    public static void main(String[] args) {
        System.out.println("1: " + lastStoneWeight(new int[]{2,7,4,1,8,1}));
        System.out.println("2: " + lastStoneWeight(new int[]{1}));
    }
}
