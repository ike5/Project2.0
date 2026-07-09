/** Copy List With Random Pointer.
 *
 *  06 Linked List - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/05-copy-list-with-random-pointer/Solution.java
 *      java -cp /tmp/out Solution
 */
import java.util.*;

public class Solution {

    public static class ListNode {
        int val;
        ListNode next;
        ListNode random;   // only used by the copy-random-pointer problem
        ListNode(int v) { val = v; }
        ListNode(int v, ListNode n) { val = v; next = n; }
    }

    private static ListNode buildList(int[] a) {
        ListNode head = null, tail = null;
        for (int v : a) {
            ListNode n = new ListNode(v);
            if (head == null) { head = n; tail = n; }
            else { tail.next = n; tail = n; }
        }
        return head;
    }

    private static int[] toArrayList(ListNode head) {
        java.util.List<Integer> out = new java.util.ArrayList<>();
        for (ListNode n = head; n != null; n = n.next) out.add(n.val);
        int[] arr = new int[out.size()];
        for (int i = 0; i < out.size(); i++) arr[i] = out.get(i);
        return arr;
    }

    public static ListNode copyRandomList(ListNode head) {
            if (head == null) return null;
            // 1) interleave
            ListNode cur = head;
            while (cur != null) {
                ListNode clone = new ListNode(cur.val);
                clone.next = cur.next;
                cur.next = clone;
                cur = clone.next;
            }
            // 2) wire random
            cur = head;
            while (cur != null) {
                if (cur.random != null) cur.next.random = cur.random.next;
                cur = cur.next.next;
            }
            // 3) split
            ListNode newHead = head.next;
            cur = head;
            while (cur != null) {
                ListNode nxt = cur.next;
                cur.next = nxt.next;
                cur = nxt.next;
            }
            return newHead;
    }

    public static void main(String[] args) {
        System.out.println("copyRandomList ready");
    }
}
