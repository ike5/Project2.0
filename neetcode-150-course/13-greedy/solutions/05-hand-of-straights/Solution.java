/** Hand of Straights.
 *
 *  13 Greedy - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-hand-of-straights/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static boolean isNStraightHand(int[] hand, int groupSize) {
            if (hand.length % groupSize != 0) return false;
            Arrays.sort(hand);
            Map<Integer, Integer> count = new HashMap<>();
            for (int x : hand) count.merge(x, 1, Integer::sum);
            for (int x : hand) {
                int c = count.getOrDefault(x, 0);
                if (c == 0) continue;
                for (int i = 0; i < groupSize; i++) {
                    int k = x + i;
                    if (count.getOrDefault(k, 0) < c) return false;
                    count.merge(k, -c, Integer::sum);
                }
            }
            return true;
    }

    public static void main(String[] args) {
        System.out.println("1: " + isNStraightHand(new int[]{1,2,3,6,2,3,4,7,8}, 3));
        System.out.println("2: " + isNStraightHand(new int[]{1,2,3,4,5}, 4));
    }
}
