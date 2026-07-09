/** Palindromic Substrings.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-palindromic-substrings/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int countSubstrings(String s) {
            int count = 0;
            for (int i = 0; i < s.length(); i++) {
                count += expand(s, i, i);
                count += expand(s, i, i + 1);
            }
            return count;
    }

    private static int expand(String s, int l, int r) {
        int c = 0;
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            c++;
            l--; r++;
        }
        return c;
    }

    public static void main(String[] args) {
        System.out.println("1: " + countSubstrings("abc"));
        System.out.println("2: " + countSubstrings("aaa"));
    }
}
