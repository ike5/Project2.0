/** Valid Palindrome.
 *
 *  02 Two Pointers - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-valid-palindrome/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean isPalindrome(String s) {
            int l = 0, r = s.length() - 1;
            while (l < r) {
                while (l < r && !Character.isLetterOrDigit(s.charAt(l))) l++;
                while (l < r && !Character.isLetterOrDigit(s.charAt(r))) r--;
                if (Character.toLowerCase(s.charAt(l)) != Character.toLowerCase(s.charAt(r))) {
                    return false;
                }
                l++;
                r--;
            }
            return true;
    }

    public static void main(String[] args) {
        System.out.println("1: " + isPalindrome("A man, a plan, a canal: Panama"));
        System.out.println("2: " + isPalindrome("race a car"));
        System.out.println("3: " + isPalindrome(" "));
        System.out.println("4: " + isPalindrome("a"));
    }
}
