/** Time Based Key-Value Store.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-time-based-key-value-store/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

        private final Map<String, List<int[]>> map = new HashMap<>();
        // each int[] is [timestamp, valueHash] — we store String separately
        private final Map<String, List<String>> values = new HashMap<>();

        public void set(String key, String value, int timestamp) {
            map.computeIfAbsent(key, k -> new ArrayList<>()).add(new int[]{timestamp, 0});
            values.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
        }

        public String get(String key, int timestamp) {
            List<int[]> times = map.get(key);
            if (times == null) return "";
            int lo = 0, hi = times.size() - 1;
            String best = "";
            while (lo <= hi) {
                int mid = (lo + hi) / 2;
                if (times.get(mid)[0] <= timestamp) {
                    best = values.get(key).get(mid);
                    lo = mid + 1;
                } else {
                    hi = mid - 1;
                }
            }
            return best;
        }

    public static void main(String[] args) {
        System.out.println("TimeMap ready");
    }
}
