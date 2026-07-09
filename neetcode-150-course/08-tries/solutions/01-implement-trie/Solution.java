/** Implement Trie (Prefix Tree).
 *
 *  08 Tries - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/01-implement-trie/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

        private final Node root = new Node();
        public void insert(String word) {
            Node n = root;
            for (int i = 0; i < word.length(); i++) {
                int c = word.charAt(i) - 'a';
                if (n.children[c] == null) n.children[c] = new Node();
                n = n.children[c];
            }
            n.isEnd = true;
        }
        public boolean search(String word) {
            Node n = find(word);
            return n != null && n.isEnd;
        }
        public boolean startsWith(String prefix) {
            return find(prefix) != null;
        }
        private Node find(String s) {
            Node n = root;
            for (int i = 0; i < s.length(); i++) {
                int c = s.charAt(i) - 'a';
                if (n.children[c] == null) return null;
                n = n.children[c];
            }
            return n;
        }
        private static class Node {
            Node[] children = new Node[26];
            boolean isEnd;
        }

    public static void main(String[] args) {
        System.out.println("Trie ready");
    }
}
