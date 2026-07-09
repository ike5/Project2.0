/** Valid Anagram.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-valid-anagram/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean isAnagram(String s, String t) {
            if (s.length() != t.length()) return false;
            int[] count = new int[26];
            for (int i = 0; i < s.length(); i++) {
                count[s.charAt(i) - 'a']++;
                count[t.charAt(i) - 'a']--;
            }
            for (int c : count) if (c != 0) return false;
            return true;
    }

    public static void main(String[] args) {
        System.out.println("1: " + isAnagram("anagram", "nagaram"));
        System.out.println("2: " + isAnagram("rat", "car"));
        System.out.println("3: " + isAnagram("a", "a"));
        System.out.println("4: " + isAnagram("ab", "a"));
        System.out.println("5: " + isAnagram("", ""));
    }
}
