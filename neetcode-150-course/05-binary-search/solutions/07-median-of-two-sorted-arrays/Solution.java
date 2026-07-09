/** Median of Two Sorted Arrays.
 *
 *  05 Binary Search - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-median-of-two-sorted-arrays/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static double findMedianSortedArrays(int[] nums1, int[] nums2) {
            if (nums1.length > nums2.length) { int[] t = nums1; nums1 = nums2; nums2 = t; }
            int m = nums1.length, n = nums2.length;
            int lo = 0, hi = m;
            while (lo <= hi) {
                int i = (lo + hi) / 2;
                int j = (m + n + 1) / 2 - i;
                int left1 = (i == 0) ? Integer.MIN_VALUE : nums1[i - 1];
                int right1 = (i == m) ? Integer.MAX_VALUE : nums1[i];
                int left2 = (j == 0) ? Integer.MIN_VALUE : nums2[j - 1];
                int right2 = (j == n) ? Integer.MAX_VALUE : nums2[j];
                if (left1 <= right2 && left2 <= right1) {
                    if (((m + n) & 1) == 1) return Math.max(left1, left2);
                    return (Math.max(left1, left2) + Math.min(right1, right2)) / 2.0;
                }
                if (left1 > right2) hi = i - 1;
                else lo = i + 1;
            }
            return 0.0;
    }

    public static void main(String[] args) {
        System.out.println("1: " + findMedianSortedArrays(new int[]{1,3}, new int[]{2}));
        System.out.println("2: " + findMedianSortedArrays(new int[]{1,2}, new int[]{3,4}));
    }
}
