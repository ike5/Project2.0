/** Longest Increasing Subsequence.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/11-longest-increasing-subsequence/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int lengthOfLIS(int[] nums) {
            int[] tails = new int[nums.length];
            int size = 0;
            for (int x : nums) {
                int lo = 0, hi = size;
                while (lo < hi) {
                    int mid = (lo + hi) / 2;
                    if (tails[mid] < x) lo = mid + 1; else hi = mid;
                }
                tails[lo] = x;
                if (lo == size) size++;
            }
            return size;
    }

    public static void main(String[] args) {
        System.out.println("1: " + lengthOfLIS(new int[]{10,9,2,5,3,7,101,18}));
        System.out.println("2: " + lengthOfLIS(new int[]{0,1,0,3,2,3}));
    }
}
