/** Daily Temperatures.
 *
 *  04 Stack - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-daily-temperatures/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] dailyTemperatures(int[] temperatures) {
            int n = temperatures.length;
            int[] answer = new int[n];
            Deque<Integer> stack = new ArrayDeque<>();   // indices, decreasing temps
            for (int i = 0; i < n; i++) {
                while (!stack.isEmpty() && temperatures[stack.peek()] < temperatures[i]) {
                    int j = stack.pop();
                    answer[j] = i - j;
                }
                stack.push(i);
            }
            return answer;
    }

    public static void main(String[] args) {
        System.out.println("1: " + Arrays.toString(dailyTemperatures(new int[]{73,74,75,71,69,72,76,73})));
        System.out.println("2: " + Arrays.toString(dailyTemperatures(new int[]{30,40,50,60})));
    }
}
