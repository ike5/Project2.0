/** Evaluate Reverse Polish Notation.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-evaluate-reverse-polish-notation/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int evalRPN(String[] tokens) {
            Deque<Integer> stack = new ArrayDeque<>();
            for (String t : tokens) {
                switch (t) {
                    case "+" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a + b); }
                    case "-" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a - b); }
                    case "*" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a * b); }
                    case "/" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a / b); }
                    default  -> stack.push(Integer.parseInt(t));
                }
            }
            return stack.pop();
    }

    public static void main(String[] args) {
        System.out.println("1: " + evalRPN(new String[]{"2","1","+","3","*"}));
        System.out.println("2: " + evalRPN(new String[]{"4","13","5","/","+"}));
    }
}
