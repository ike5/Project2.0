/** Word Search II.
 *
 *  08 Tries - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/03-word-search-ii/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static class TrieNode {
        TrieNode[] children = new TrieNode[26];
        String word;
    }

    public static void trieDfs(char[][] board, int r, int c, TrieNode n, java.util.List<String> out) {
        if (n == null) return;
        char ch = board[r][c];
        if (ch == '#') return;
        TrieNode child = n.children[ch - 'a'];
        if (child == null) return;
        if (child.word != null) {
            out.add(child.word);
            child.word = null;
        }
        board[r][c] = '#';
        if (r > 0)                 trieDfs(board, r - 1, c, child, out);
        if (c > 0)                 trieDfs(board, r, c - 1, child, out);
        if (r < board.length - 1)  trieDfs(board, r + 1, c, child, out);
        if (c < board[0].length - 1) trieDfs(board, r, c + 1, child, out);
        board[r][c] = ch;
    }

    public static List<String> findWords(char[][] board, String[] words) {
            // build trie
            TrieNode root = new TrieNode();
            for (String w : words) {
                TrieNode n = root;
                for (int i = 0; i < w.length(); i++) {
                    int c = w.charAt(i) - 'a';
                    if (n.children[c] == null) n.children[c] = new TrieNode();
                    n = n.children[c];
                }
                n.word = w;
            }
            int rows = board.length, cols = board[0].length;
            List<String> out = new ArrayList<>();
            for (int r = 0; r < rows; r++) {
                for (int c = 0; c < cols; c++) {
                    trieDfs(board, r, c, root, out);
                }
            }
            return out;
    }

    public static void main(String[] args) {
        System.out.println("findWords ready");
    }
}
