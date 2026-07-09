# Lab 09 — Heap / Priority Queue

**You'll:** implement *Kth Largest in a Stream* and *Last Stone Weight* in
both languages. ⏱️ ~1 h.

---

## Part A — *Kth Largest in a Stream* in Python

```python
import heapq

class KthLargest:
    def __init__(self, k, nums):
        # your code
        ...

    def add(self, val):
        ...


if __name__ == "__main__":
    kl = KthLargest(3, [4, 5, 8, 2])
    assert kl.add(3) == 4
    assert kl.add(5) == 5
    assert kl.add(10) == 5
    assert kl.add(9) == 8
    assert kl.add(4) == 8
    print("all tests passed")
```

**Walk-through:** a min-heap of size k.

```python
class KthLargest:
    def __init__(self, k, nums):
        self.k = k
        self.heap = []
        for n in nums:
            self.add(n)

    def add(self, val):
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]
```

The smallest of the k largest is the kth largest. Keep the heap at size
k, and `heap[0]` is the answer.

## Part B — *Kth Largest in a Stream* in Java 21

```java
import java.util.PriorityQueue;

public class LabKthLargest {
    public static class KthLargest {
        private final int k;
        private final PriorityQueue<Integer> heap = new PriorityQueue<>();

        public KthLargest(int k, int[] nums) {
            this.k = k;
            for (int n : nums) add(n);
        }

        public int add(int val) {
            heap.offer(val);
            if (heap.size() > k) heap.poll();
            return heap.peek();
        }
    }

    public static void main(String[] args) {
        KthLargest kl = new KthLargest(3, new int[]{4, 5, 8, 2});
        assert kl.add(3) == 4;
        assert kl.add(5) == 5;
        assert kl.add(10) == 5;
        assert kl.add(9) == 8;
        assert kl.add(4) == 8;
        System.out.println("all tests passed");
    }
}
```

## Part C — *Last Stone Weight* in Python

```python
import heapq

def last_stone_weight(stones):
    ...


if __name__ == "__main__":
    assert last_stone_weight([2, 7, 4, 1, 8, 1]) == 1
    assert last_stone_weight([1]) == 1
    assert last_stone_weight([2, 2]) == 0
    print("all tests passed")
```

**Walk-through:** max-heap via negation.

```python
def last_stone_weight(stones):
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        a = -heapq.heappop(heap)
        b = -heapq.heappop(heap)
        if a != b:
            heapq.heappush(heap, -(a - b))
    return -heap[0] if heap else 0
```

## Part D — *Last Stone Weight* in Java 21

```java
import java.util.Comparator;
import java.util.PriorityQueue;

public class LabLastStone {
    public static int lastStoneWeight(int[] stones) {
        PriorityQueue<Integer> heap = new PriorityQueue<>(Comparator.reverseOrder());
        for (int s : stones) heap.offer(s);
        while (heap.size() > 1) {
            int a = heap.poll(), b = heap.poll();
            if (a != b) heap.offer(a - b);
        }
        return heap.isEmpty() ? 0 : heap.poll();
    }

    public static void main(String[] args) {
        assert lastStoneWeight(new int[]{2, 7, 4, 1, 8, 1}) == 1;
        assert lastStoneWeight(new int[]{1}) == 1;
        assert lastStoneWeight(new int[]{2, 2}) == 0;
        System.out.println("all tests passed");
    }
}
```

## What you learned

- **`heapq` is a min-heap.** Negate to get a max-heap.
- **`PriorityQueue` is a min-heap.** Pass `Comparator.reverseOrder()` for a max-heap.
- **Heap of size k** is the workhorse for top-k problems.

➡️ **[challenge.md](./challenge.md)**
