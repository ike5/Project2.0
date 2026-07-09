/** Meeting Rooms II.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-meeting-rooms-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int minMeetingRooms(int[][] intervals) {
            int n = intervals.length;
            int[] starts = new int[n], ends = new int[n];
            for (int i = 0; i < n; i++) { starts[i] = intervals[i][0]; ends[i] = intervals[i][1]; }
            Arrays.sort(starts); Arrays.sort(ends);
            int rooms = 0, endPtr = 0;
            for (int s : starts) {
                if (s >= ends[endPtr]) endPtr++;
                else rooms++;
            }
            return rooms;
    }

    public static void main(String[] args) {
        System.out.println("minMeetingRooms ready");
    }
}
