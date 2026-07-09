/** Valid Parenthesis String.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/08-valid-parenthesis-string/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean checkValidString(String s) {
            int lo = 0, hi = 0;
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i);
                if (c == '(') { lo++; hi++; }
                else if (c == ')') { lo = Math.max(lo - 1, 0); hi--; }
                else { lo = Math.max(lo - 1, 0); hi++; }
                if (hi < 0) return false;
            }
            return lo == 0;
    }

    public static void main(String[] args) {
        System.out.println("1: " + checkValidString("()"));
        System.out.println("2: " + checkValidString("(*)"));
    }
}
