/** Word Ladder.
 *
 *  11 Graphs - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/13-word-ladder/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static int ladderLength(String beginWord, String endWord, List<String> wordList) {
            Set<String> wordSet = new HashSet<>(wordList);
            if (!wordSet.contains(endWord)) return 0;
            Deque<String> q = new ArrayDeque<>();
            q.offer(beginWord);
            Set<String> visited = new HashSet<>();
            visited.add(beginWord);
            int depth = 1;
            int L = beginWord.length();
            while (!q.isEmpty()) {
                int size = q.size();
                for (int i = 0; i < size; i++) {
                    String word = q.poll();
                    if (word.equals(endWord)) return depth;
                    char[] arr = word.toCharArray();
                    for (int j = 0; j < L; j++) {
                        char orig = arr[j];
                        for (char c = 'a'; c <= 'z'; c++) {
                            if (c == orig) continue;
                            arr[j] = c;
                            String nw = new String(arr);
                            if (wordSet.contains(nw) && !visited.contains(nw)) {
                                visited.add(nw);
                                q.offer(nw);
                            }
                        }
                        arr[j] = orig;
                    }
                }
                depth++;
            }
            return 0;
    }

    public static void main(String[] args) {
        System.out.println("ladderLength ready");
    }
}
