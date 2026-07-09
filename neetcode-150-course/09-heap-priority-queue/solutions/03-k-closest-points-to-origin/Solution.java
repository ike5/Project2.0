/** K Closest Points to Origin.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-k-closest-points-to-origin/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[][] kClosest(int[][] points, int k) {
            PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> {
                int da = a[0] * a[0] + a[1] * a[1];
                int db = b[0] * b[0] + b[1] * b[1];
                return Integer.compare(db, da);  // max-heap on distance;
            });
            for (int[] p : points) {
                heap.offer(p);
                if (heap.size() > k) heap.poll();
            }
            int[][] out = new int[heap.size()][];
            return heap.toArray(out);
    }

    public static void main(String[] args) {
        System.out.println("1: " + Arrays.toString(kClosest(new int[][]{{1,3},{-2,2}}, 2)));
    }
}
