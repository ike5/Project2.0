/** Letter Combinations of a Phone Number.
 *
 *  10 Backtracking - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/08-letter-combinations-of-a-phone-number/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static List<String> letterCombinations(String digits) {
            if (digits.isEmpty()) return List.of();
            String[] map = {"abc","def","ghi","jkl","mno","pqrs","tuv","wxyz"};
            List<String> out = new ArrayList<>();
            backtrack(out, map, digits, 0, new StringBuilder());
            return out;
    }

    private static void backtrack(List<String> out, String[] map, String digits, int i, StringBuilder path) {
        if (i == digits.length()) { out.add(path.toString()); return; }
        String letters = map[digits.charAt(i) - '2'];
        for (int k = 0; k < letters.length(); k++) {
            path.append(letters.charAt(k));
            backtrack(out, map, digits, i + 1, path);
            path.deleteCharAt(path.length() - 1);
        }
    }

    public static void main(String[] args) {
        System.out.println("letterCombinations ready");
    }
}
