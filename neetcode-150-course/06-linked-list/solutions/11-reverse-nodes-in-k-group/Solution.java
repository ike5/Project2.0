/** Reverse Nodes in k-Group.
 *
 *  06 Linked List - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/11-reverse-nodes-in-k-group/Solution.java
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

    public static ListNode reverseKGroup(ListNode head, int k) {
            ListNode dummy = new ListNode(0);
            dummy.next = head;
            ListNode groupPrev = dummy;
            while (true) {
                ListNode kth = groupPrev;
                for (int i = 0; i < k; i++) {
                    kth = kth.next;
                    if (kth == null) return dummy.next;
                }
                ListNode groupNext = kth.next;
                // reverse
                ListNode prev = null, curr = groupPrev.next;
                for (int i = 0; i < k; i++) {
                    ListNode nxt = curr.next;
                    curr.next = prev;
                    prev = curr;
                    curr = nxt;
                }
                // reconnect
                ListNode oldHead = groupPrev.next;
                groupPrev.next = prev;
                oldHead.next = groupNext;
                groupPrev = oldHead;
            }
    }

    public static void main(String[] args) {
        System.out.println("reverseKGroup ready");
    }
}
