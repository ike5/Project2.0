/** LRU Cache.
 *
 *  06 Linked List - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/09-lru-cache/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static class LRUCache {
        private final int cap;
        private final Map<Integer, Node> map = new HashMap<>();
        private final Node head = new Node(0, 0);   // sentinel
        private final Node tail = new Node(0, 0);   // sentinel

        public LRUCache(int capacity) {
            this.cap = capacity;
            head.next = tail;
            tail.prev = head;
        }

        public int get(int key) {
            Node n = map.get(key);
            if (n == null) return -1;
            moveToFront(n);
            return n.val;
        }

        public void put(int key, int value) {
            Node n = map.get(key);
            if (n != null) {
                n.val = value;
                moveToFront(n);
            } else {
                if (map.size() == cap) {
                    Node lru = tail.prev;
                    map.remove(lru.key);
                    unlink(lru);
                }
                Node fresh = new Node(key, value);
                map.put(key, fresh);
                insertAfterHead(fresh);
            }
        }

        private void moveToFront(Node n) {
            unlink(n);
            insertAfterHead(n);
        }

        private void unlink(Node n) {
            n.prev.next = n.next;
            n.next.prev = n.prev;
        }

        private void insertAfterHead(Node n) {
            n.next = head.next;
            n.prev = head;
            head.next.prev = n;
            head.next = n;
        }

        private static class Node {
            int key, val;
            Node prev, next;
            Node(int k, int v) { key = k; val = v; }
        }
    }

    public static void main(String[] args) {
        System.out.println("get ready");
    }
}
