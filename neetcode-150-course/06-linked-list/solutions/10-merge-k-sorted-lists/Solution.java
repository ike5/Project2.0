/** Merge K Sorted Lists.
 *
 *  06 Linked List - auto-generated solution.
 *
 *  Run:
 *      mkdir -p /tmp/out
 *      javac -d /tmp/out solutions/10-merge-k-sorted-lists/Solution.java
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

    public static ListNode mergeKLists(ListNode[] lists) {
            PriorityQueue<ListNode> pq = new PriorityQueue<>(
                (a, b) -> Integer.compare(a.val, b.val)
            );
            for (ListNode n : lists) if (n != null) pq.offer(n);
            ListNode dummy = new ListNode(0);
            ListNode tail = dummy;
            while (!pq.isEmpty()) {
                ListNode n = pq.poll();
                tail.next = n;
                tail = tail.next;
                if (n.next != null) pq.offer(n.next);
            }
            return dummy.next;
    }

    public static void main(String[] args) {
        System.out.println("mergeKLists ready");
    }
}
