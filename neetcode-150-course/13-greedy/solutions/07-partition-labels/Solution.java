/** Partition Labels.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-partition-labels/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<Integer> partitionLabels(String s) {
            int[] last = new int[26];
            for (int i = 0; i < s.length(); i++) last[s.charAt(i) - 'a'] = i;
            List<Integer> out = new ArrayList<>();
            int start = 0, end = 0;
            for (int i = 0; i < s.length(); i++) {
                end = Math.max(end, last[s.charAt(i) - 'a']);
                if (i == end) { out.add(end - start + 1); start = i + 1; }
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("1: " + partitionLabels("ababcbacadefegdehijhklij"));
    }
}
