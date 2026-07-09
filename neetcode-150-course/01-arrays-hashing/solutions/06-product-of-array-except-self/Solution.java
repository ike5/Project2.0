/** Product of Array Except Self.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/06-product-of-array-except-self/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int[] productExceptSelf(int[] nums) {
            int n = nums.length;
            int[] answer = new int[n];
            int p = 1;
            for (int i = 0; i < n; i++) { answer[i] = p; p *= nums[i]; }
            int s = 1;
            for (int i = n - 1; i >= 0; i--) { answer[i] *= s; s *= nums[i]; }
            return answer;
    }

    public static void main(String[] args) {
        System.out.println("1: " + Arrays.toString(productExceptSelf(new int[]{1,2,3,4})));
        System.out.println("2: " + Arrays.toString(productExceptSelf(new int[]{-1,1,0,-3,3})));
        System.out.println("3: " + Arrays.toString(productExceptSelf(new int[]{2, 3})));
    }
}
