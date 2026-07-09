/** Longest Palindromic Substring.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-longest-palindromic-substring/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static String longestPalindrome(String s) {
            int bestLo = 0, bestLen = 0;
            for (int i = 0; i < s.length(); i++) {
                int l1 = expand(s, i, i);
                int l2 = expand(s, i, i + 1);
                int m = Math.max(l1, l2);
                if (m > bestLen) {
                    bestLen = m;
                    bestLo = i - (m - 1) / 2;
                }
            }
            return s.substring(bestLo, bestLo + bestLen);
    }

    private static int expand(String s, int l, int r) {
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            l--; r++;
        }
        return r - l - 1;
    }

    public static void main(String[] args) {
        System.out.println("1: " + longestPalindrome("babad"));
        System.out.println("2: " + longestPalindrome("cbbd"));
    }
}
