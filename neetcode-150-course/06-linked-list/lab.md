# Lab 06 — Linked List

**You'll:** implement *Reverse Linked List* and *Merge Two Sorted Lists* in
both languages, then build helper utilities for converting arrays to lists
and back. ⏱️ ~1.5 h.

---

## Part A — *Reverse Linked List* in Python

Create `06-linked-list/lab_reverse.py`:

```python
class ListNode:
    def __init__(self, val=0, nxt=None):
        self.val = val
        self.next = nxt


def build_list(values):
    head = None
    tail = None
    for v in values:
        n = ListNode(v)
        if head is None:
            head = n; tail = n
        else:
            tail.next = n
            tail = n
    return head


def to_array(head):
    out = []
    while head is not None:
        out.append(head.val)
        head = head.next
    return out


def reverse_list(head):
    # your code
    ...


if __name__ == "__main__":
    assert to_array(reverse_list(build_list([1, 2, 3, 4, 5]))) == [5, 4, 3, 2, 1]
    assert to_array(reverse_list(build_list([1, 2]))) == [2, 1]
    assert to_array(reverse_list(build_list([]))) == []
    print("all tests passed")
```

**Walk-through:**

```python
def reverse_list(head):
    prev = None
    curr = head
    while curr is not None:
        nxt = curr.next
        curr.next = prev
        prev = curr
        curr = nxt
    return prev
```

Three pointers: `prev` (the new tail so far), `curr` (the current node),
`nxt` (saved *before* we overwrite `curr.next`).

✅ Run it.

## Part B — *Reverse Linked List* in Java 21

```java
public class LabReverse {
    public static class ListNode {
        int val;
        ListNode next;
        ListNode(int v) { val = v; }
    }

    public static ListNode buildList(int[] a) {
        ListNode head = null, tail = null;
        for (int v : a) {
            ListNode n = new ListNode(v);
            if (head == null) { head = n; tail = n; }
            else { tail.next = n; tail = n; }
        }
        return head;
    }

    public static int[] toArray(ListNode head) {
        java.util.List<Integer> out = new java.util.ArrayList<>();
        for (ListNode n = head; n != null; n = n.next) out.add(n.val);
        int[] arr = new int[out.size()];
        for (int i = 0; i < out.size(); i++) arr[i] = out.get(i);
        return arr;
    }

    public static ListNode reverseList(ListNode head) {
        // your code
    }

    public static void main(String[] args) {
        assert java.util.Arrays.equals(
            toArray(reverseList(buildList(new int[]{1, 2, 3, 4, 5}))),
            new int[]{5, 4, 3, 2, 1}
        );
        assert java.util.Arrays.equals(
            toArray(reverseList(buildList(new int[]{1, 2}))),
            new int[]{2, 1}
        );
        assert java.util.Arrays.equals(
            toArray(reverseList(buildList(new int[]{}))),
            new int[]{}
        );
        System.out.println("all tests passed");
    }
}
```

**Walk-through:**

```java
public static ListNode reverseList(ListNode head) {
    ListNode prev = null;
    ListNode curr = head;
    while (curr != null) {
        ListNode nxt = curr.next;
        curr.next = prev;
        prev = curr;
        curr = nxt;
    }
    return prev;
}
```

`null` is Java's `None`. The `nxt` save is critical — without it, after
`curr.next = prev` we lose the rest of the list.

## Part C — *Merge Two Sorted Lists* in Python

```python
def merge_two_lists(list1, list2):
    dummy = ListNode(0)
    tail = dummy
    while list1 is not None and list2 is not None:
        if list1.val <= list2.val:
            tail.next = list1
            list1 = list1.next
        else:
            tail.next = list2
            list2 = list2.next
        tail = tail.next
    tail.next = list1 if list1 is not None else list2
    return dummy.next


if __name__ == "__main__":
    a = build_list([1, 2, 4])
    b = build_list([1, 3, 4])
    assert to_array(merge_two_lists(a, b)) == [1, 1, 2, 3, 4, 4]
    assert to_array(merge_two_lists(None, None)) == []
    assert to_array(merge_two_lists(None, build_list([0]))) == [0]
    print("all tests passed")
```

## Part D — *Merge Two Sorted Lists* in Java 21

```java
public static ListNode mergeTwoLists(ListNode list1, ListNode list2) {
    ListNode dummy = new ListNode(0);
    ListNode tail = dummy;
    while (list1 != null && list2 != null) {
        if (list1.val <= list2.val) {
            tail.next = list1;
            list1 = list1.next;
        } else {
            tail.next = list2;
            list2 = list2.next;
        }
        tail = tail.next;
    }
    tail.next = (list1 != null) ? list1 : list2;
    return dummy.next;
}
```

## What you learned

- **The `prev/curr/nxt` triple** for in-place reverse.
- **The dummy head** trick to avoid special-casing the first node.
- **Building a list from an array** is a small but essential helper.
- **Walking a list in Java** uses `for (n = head; n != null; n = n.next)`.

➡️ **[challenge.md](./challenge.md)** then the [problems/](./problems/) in order.
