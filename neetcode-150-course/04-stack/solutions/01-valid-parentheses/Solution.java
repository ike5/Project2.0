/** Valid Parentheses.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-valid-parentheses/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean isValid(String s) {
            Map<Character, Character> pairs = Map.of(
                ')', '(', ']', '[', '}', '{'
            );
            Deque<Character> stack = new ArrayDeque<>();
            for (int i = 0; i < s.length(); i++) {
                char c = s.charAt(i);
                if (pairs.containsKey(c)) {
                    if (stack.isEmpty() || stack.peek() != pairs.get(c)) return false;
                    stack.pop();
                } else {
                    stack.push(c);
                }
            }
            return stack.isEmpty();
    }

    public static void main(String[] args) {
        System.out.println("1: " + isValid("()[]{}"));
        System.out.println("2: " + isValid("(]"));
        System.out.println("3: " + isValid("([)]"));
        System.out.println("4: " + isValid("{[]}"));
    }
}
