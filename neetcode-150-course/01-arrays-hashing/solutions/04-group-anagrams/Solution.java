/** Group Anagrams.
 *
 *  01 Arrays Hashing - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-group-anagrams/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<List<String>> groupAnagrams(String[] strs) {
            Map<String, List<String>> groups = new HashMap<>();
            for (String s : strs) {
                char[] chars = s.toCharArray();
                Arrays.sort(chars);
                String key = new String(chars);
                groups.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
            }
            return new ArrayList<>(groups.values());
    }

    public static void main(String[] args) {
        System.out.println("1: " + groupAnagrams(new String[]{"eat","tea","tan","ate","nat","bat"}));
        System.out.println("2: " + groupAnagrams(new String[]{ "" }));
        System.out.println("3: " + groupAnagrams(new String[]{"a"}));
    }
}
