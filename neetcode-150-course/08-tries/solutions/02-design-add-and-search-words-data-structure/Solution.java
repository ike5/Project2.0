/** Design Add and Search Words Data Structure.
 *
 *  08 Tries - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/02-design-add-and-search-words-data-structure/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

        private final Node root = new Node();
        public void addWord(String word) {
            Node n = root;
            for (int i = 0; i < word.length(); i++) {
                int c = word.charAt(i) - 'a';
                if (n.children[c] == null) n.children[c] = new Node();
                n = n.children[c];
            }
            n.isEnd = true;
        }
        public boolean search(String word) {
            return dfs(root, word, 0);
        }
        private boolean dfs(Node n, String word, int i) {
            if (n == null) return false;
            if (i == word.length()) return n.isEnd;
            char c = word.charAt(i);
            if (c == '.') {
                for (Node child : n.children) if (dfs(child, word, i + 1)) return true;
                return false;
            }
            return dfs(n.children[c - 'a'], word, i + 1);
        }
        private static class Node {
            Node[] children = new Node[26];
            boolean isEnd;
        }

    public static void main(String[] args) {
        System.out.println("WordDictionary ready");
    }
}
