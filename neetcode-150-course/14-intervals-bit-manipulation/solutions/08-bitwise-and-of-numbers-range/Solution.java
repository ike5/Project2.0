/** Bitwise AND of Numbers Range.
 *
 *  14 Intervals Bit Manipulation - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/08-bitwise-and-of-numbers-range/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int rangeBitwiseAnd(int left, int right) {
            int shift = 0;
            while (left != right) {
                left >>>= 1;
                right >>>= 1;
                shift++;
            }
            return left << shift;
    }

    public static void main(String[] args) {
        System.out.println("rangeBitwiseAnd ready");
    }
}
