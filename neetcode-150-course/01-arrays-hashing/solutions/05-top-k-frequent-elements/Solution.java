/** Top K Frequent Elements.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-top-k-frequent-elements/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<Integer> topKFrequent(int[] nums, int k) {
            Map<Integer, Integer> count = new HashMap<>();
            for (int x : nums) count.merge(x, 1, Integer::sum);
            // bucket sort by frequency; max freq is nums.length
            List<Integer>[] buckets = new List[nums.length + 1];
            for (int i = 0; i < buckets.length; i++) buckets[i] = new ArrayList<>();
            for (var e : count.entrySet()) buckets[e.getValue()].add(e.getKey());
            List<Integer> out = new ArrayList<>();
            for (int f = buckets.length - 1; f >= 0 && out.size() < k; f--) {
                out.addAll(buckets[f]);
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("1: " + topKFrequent(new int[]{1,1,1,2,2,3}, 2));
        System.out.println("2: " + topKFrequent(new int[]{1}, 1));
    }
}
