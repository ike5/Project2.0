/** Car Fleet.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-car-fleet/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int carFleet(int target, int[] position, int[] speed) {
            int n = position.length;
            Integer[] idx = new Integer[n];
            for (int i = 0; i < n; i++) idx[i] = i;
            Arrays.sort(idx, (a, b) -> Integer.compare(position[b], position[a]));
            int fleets = 0;
            double curTime = 0.0;
            for (int i : idx) {
                double time = (double)(target - position[i]) / speed[i];
                if (time > curTime) {
                    fleets++;
                    curTime = time;
                }
            }
            return fleets;
    }

    public static void main(String[] args) {
        System.out.println("1: " + carFleet(12, new int[]{10,8,0,5,3}, new int[]{2,4,1,1,3}));
        System.out.println("2: " + carFleet(10, new int[]{3}, new int[]{3}));
    }
}
