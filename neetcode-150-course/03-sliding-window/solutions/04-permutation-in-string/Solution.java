/** Permutation in String.
 *
 *  03 Sliding Window - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-permutation-in-string/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean checkInclusion(String s1, String s2) {
            if (s1.length() > s2.length()) return false;
            int[] need = new int[26], have = new int[26];
            for (int i = 0; i < s1.length(); i++) need[s1.charAt(i) - 'a']++;
            for (int i = 0; i < s1.length(); i++) have[s2.charAt(i) - 'a']++;
            if (Arrays.equals(need, have)) return true;
            for (int i = s1.length(); i < s2.length(); i++) {
                have[s2.charAt(i) - 'a']++;
                have[s2.charAt(i - s1.length()) - 'a']--;
                if (Arrays.equals(need, have)) return true;
            }
            return false;
    }

    public static void main(String[] args) {
        System.out.println("1: " + checkInclusion("ab", "eidbaooo"));
        System.out.println("2: " + checkInclusion("ab", "eidboaoo"));
    }
}
