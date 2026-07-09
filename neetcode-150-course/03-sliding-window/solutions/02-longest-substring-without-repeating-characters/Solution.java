/** Longest Substring Without Repeating Characters.
 *
 *  03 Sliding Window - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-longest-substring-without-repeating-characters/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int lengthOfLongestSubstring(String s) {
            int[] last = new int[128];
            Arrays.fill(last, -1);
            int best = 0;
            for (int r = 0, l = 0; r < s.length(); r++) {
                char c = s.charAt(r);
                if (last[c] >= l) l = last[c] + 1;
                last[c] = r;
                best = Math.max(best, r - l + 1);
            }
            return best;
    }

    public static void main(String[] args) {
        System.out.println("1: " + lengthOfLongestSubstring("abcabcbb"));
        System.out.println("2: " + lengthOfLongestSubstring("bbbbb"));
        System.out.println("3: " + lengthOfLongestSubstring("pwwkew"));
        System.out.println("4: " + lengthOfLongestSubstring(""));
    }
}
