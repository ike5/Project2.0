/** Encode and Decode Strings.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/08-encode-and-decode-strings/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static String encode(List<String> strs) {
            StringBuilder sb = new StringBuilder();
            for (String s : strs) sb.append(s.length()).append('#').append(s);
            return sb.toString();
    }

    public static void main(String[] args) {
        System.out.println("encode ready");
    }
}
