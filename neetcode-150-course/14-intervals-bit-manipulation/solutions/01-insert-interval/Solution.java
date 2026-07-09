/** Insert Interval.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-insert-interval/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[][] insert(int[][] intervals, int[] newInterval) {
            List<int[]> out = new ArrayList<>();
            for (int[] iv : intervals) {
                if (iv[1] < newInterval[0]) out.add(iv);
                else if (iv[0] > newInterval[1]) {
                    out.add(newInterval);
                    newInterval = iv;   // becomes the new "to insert"
                    // (effectively appends the rest below; cleaner with extend)
                    out.add(iv);
                    // Continue to add remaining (which we'll handle outside)
                }
                else {
                    newInterval[0] = Math.min(iv[0], newInterval[0]);
                    newInterval[1] = Math.max(iv[1], newInterval[1]);
                }
            }
            if (!out.contains(newInterval)) out.add(newInterval);
            return out.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        System.out.println("insert ready");
    }
}
