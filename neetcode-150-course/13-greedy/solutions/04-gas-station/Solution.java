/** Gas Station.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-gas-station/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int canCompleteCircuit(int[] gas, int[] cost) {
            int total = 0, tank = 0, start = 0;
            for (int i = 0; i < gas.length; i++) total += gas[i] - cost[i];
            if (total < 0) return -1;
            for (int i = 0; i < gas.length; i++) {
                tank += gas[i] - cost[i];
                if (tank < 0) { start = i + 1; tank = 0; }
            }
            return start;
    }

    public static void main(String[] args) {
        System.out.println("1: " + canCompleteCircuit(new int[]{1,2,3,4,5}, new int[]{3,4,5,1,2}));
        System.out.println("2: " + canCompleteCircuit(new int[]{2,3,4}, new int[]{3,4,3}));
    }
}
