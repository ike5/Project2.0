/** Longest Repeating Character Replacement.
 *
 *  03 Sliding Window - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-longest-repeating-character-replacement/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int characterReplacement(String s, int k) {
            int[] counts = new int[26];
            int l = 0, maxCount = 0, best = 0;
            for (int r = 0; r < s.length(); r++) {
                int idx = s.charAt(r) - 'A';
                counts[idx]++;
                maxCount = Math.max(maxCount, counts[idx]);
                while ((r - l + 1) - maxCount > k) {
                    counts[s.charAt(l) - 'A']--;
                    l++;
                }
                best = Math.max(best, r - l + 1);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + characterReplacement("ABAB", 2));
        System.out.println("2: " + characterReplacement("AABABBA", 1));
    }
}
