/** Merge Intervals.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-merge-intervals/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[][] merge(int[][] intervals) {
            Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
            List<int[]> out = new ArrayList<>();
            for (int[] iv : intervals) {
                if (!out.isEmpty() && iv[0] <= out.get(out.size() - 1)[1]) {
                    out.get(out.size() - 1)[1] = Math.max(out.get(out.size() - 1)[1], iv[1]);
                } else out.add(iv);
            }
            return out.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        System.out.println("merge ready");
    }
}
