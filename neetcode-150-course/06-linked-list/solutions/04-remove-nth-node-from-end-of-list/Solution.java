/** Remove Nth Node From End of List.
 *
 *  06 Linked List - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/04-remove-nth-node-from-end-of-list/Solution.java
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

    public static ListNode removeNthFromEnd(ListNode head, int n) {
            ListNode dummy = new ListNode(0);
            dummy.next = head;
            ListNode slow = dummy, fast = dummy;
            for (int i = 0; i < n; i++) fast = fast.next;
            while (fast.next != null) {
                slow = slow.next;
                fast = fast.next;
            }
            slow.next = slow.next.next;
            return dummy.next;
    }

    public static void main(String[] args) {
        System.out.println("removeNthFromEnd ready");
    }
}
