/** Task Scheduler.
 *
 *  09 Heap Priority Queue - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-task-scheduler/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int leastInterval(char[] tasks, int n) {
            int[] count = new int[26];
            for (char t : tasks) count[t - 'A']++;
            int maxFreq = 0;
            for (int c : count) maxFreq = Math.max(maxFreq, c);
            int nMax = 0;
            for (int c : count) if (c == maxFreq) nMax++;
            int partCount = (maxFreq - 1) * (n + 1) + nMax;
            return Math.max(tasks.length, partCount);
    }

    public static void main(String[] args) {
        System.out.println("1: " + leastInterval(new char[]{'A','A','A','B','B','B'}, 2));
        System.out.println("2: " + leastInterval(new char[]{'A','A','A','B','B','B'}, 0));
    }
}
