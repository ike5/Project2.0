/** Non-Overlapping Intervals.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-non-overlapping-intervals/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int eraseOverlapIntervals(int[][] intervals) {
            Arrays.sort(intervals, (a, b) -> Integer.compare(a[1], b[1]));
            int kept = 0;
            int end = Integer.MIN_VALUE;
            for (int[] iv : intervals) {
                if (iv[0] >= end) { kept++; end = iv[1]; }
            }
            return intervals.length - kept;
    }

    public static void main(String[] args) {
        System.out.println("eraseOverlapIntervals ready");
    }
}
