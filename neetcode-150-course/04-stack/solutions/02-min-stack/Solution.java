/** Min Stack.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-min-stack/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

        private final Deque<int[]> stack = new ArrayDeque<>();
        public void push(int x) {
            int min = stack.isEmpty() ? x : Math.min(x, stack.peek()[1]);
            stack.push(new int[] { x, min });
        }
        public void pop() { stack.pop(); }
        public int top() { return stack.peek()[0]; }
        public int getMin() { return stack.peek()[1]; }

    public static void main(String[] args) {
        System.out.println("MinStack ready");
    }
}
