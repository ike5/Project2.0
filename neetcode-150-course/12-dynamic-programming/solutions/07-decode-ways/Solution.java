/** Decode Ways.
 *
 *  12 Dynamic Programming - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/07-decode-ways/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int numDecodings(String s) {
            if (s.isEmpty() || s.charAt(0) == '0') return 0;
            int dp0 = 1, dp1 = 1;
            for (int i = 1; i < s.length(); i++) {
                int cur = 0;
                if (s.charAt(i) != '0') cur += dp1;
                int two = Integer.parseInt(s.substring(i - 1, i + 1));
                if (10 <= two && two <= 26) cur += dp0;
                dp0 = dp1;
                dp1 = cur;
            }
            return dp1;
    }

    public static void main(String[] args) {
        System.out.println("1: " + numDecodings("12"));
        System.out.println("2: " + numDecodings("226"));
    }
}
