/** Koko Eating Bananas.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-koko-eating-bananas/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int minEatingSpeed(int[] piles, int h) {
            int lo = 1, hi = 0;
            for (int p : piles) hi = Math.max(hi, p);
            while (lo < hi) {
                int mid = lo + (hi - lo) / 2;
                int hours = 0;
                for (int p : piles) hours += (p + mid - 1) / mid;
                if (hours <= h) hi = mid;
                else lo = mid + 1;
            }
            return lo;
    }

    public static void main(String[] args) {
        System.out.println("1: " + minEatingSpeed(new int[]{1,4,3,2}, 9));
        System.out.println("2: " + minEatingSpeed(new int[]{25,10,23,4}, 4));
    }
}
