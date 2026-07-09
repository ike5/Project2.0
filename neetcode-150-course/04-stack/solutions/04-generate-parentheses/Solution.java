/** Generate Parentheses.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-generate-parentheses/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<String> generateParenthesis(int n) {
            List<String> out = new ArrayList<>();
            backtrack(out, new StringBuilder(), 0, 0, n);
            return out;
    }

    private static void backtrack(List<String> out, StringBuilder sb, int opens, int closes, int n) {
        if (sb.length() == 2 * n) {
            out.add(sb.toString());
            return;
        }
        if (opens < n) {
            sb.append('(');
            backtrack(out, sb, opens + 1, closes, n);
            sb.deleteCharAt(sb.length() - 1);
        }
        if (closes < opens) {
            sb.append(')');
            backtrack(out, sb, opens, closes + 1, n);
            sb.deleteCharAt(sb.length() - 1);
        }
    }

    public static void main(String[] args) {
        System.out.println("1: " + generateParenthesis(3));
    }
}
