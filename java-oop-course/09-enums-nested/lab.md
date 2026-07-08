# Lab 09 — Rich Enums & Nested Classes

**You'll:** build a small `Operation` enum with constant-specific
behaviour and a `Direction` enum with a state machine. ⏱️ ~40 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop09 && cd ~/dev/oop09
mkdir -p src/com/example/workflow
```

## Part B — `Operation` with constant-specific `apply`

`src/com/example/workflow/Operation.java`:
```java
package com.example.workflow;

public enum Operation {
    ADD("+")      { public long apply(long a, long b) { return a + b; } },
    SUBTRACT("-") { public long apply(long a, long b) { return a - b; } },
    MULTIPLY("*") { public long apply(long a, long b) { return a * b; } },
    DIVIDE("/")   { public long apply(long a, long b) { return a / b; } };

    private final String symbol;
    Operation(String symbol) { this.symbol = symbol; }
    public String symbol() { return symbol; }
    public abstract long apply(long a, long b);
}
```

## Part C — `Direction` with state machine

`src/com/example/workflow/Direction.java`:
```java
package com.example.workflow;

public enum Direction {
    NORTH, EAST, SOUTH, WEST;

    public Direction left()      { return vals()[(ordinal() + 3) % 4]; }
    public Direction right()     { return vals()[(ordinal() + 1) % 4]; }
    public Direction opposite()  { return vals()[(ordinal() + 2) % 4]; }

    private static Direction[] vals() { return values(); }   // convenience
}
```

## Part D — A `LinkedList<E>` with a static nested `Node<E>`

`src/com/example/workflow/SimpleLinkedList.java`:
```java
package com.example.workflow;

import java.util.Iterator;
import java.util.NoSuchElementException;

public final class SimpleLinkedList<E> implements Iterable<E> {
    private Node<E> head;
    private int size;

    public void add(E e) {
        Node<E> n = new Node<>(e, null);
        if (head == null) { head = n; }
        else {
            Node<E> cur = head;
            while (cur.next != null) cur = cur.next;
            cur.next = n;
        }
        size++;
    }
    public int size() { return size; }

    @Override
    public Iterator<E> iterator() {
        return new Iterator<>() {
            Node<E> cur = head;
            @Override public boolean hasNext() { return cur != null; }
            @Override public E next() {
                if (cur == null) throw new NoSuchElementException();
                E v = cur.value;
                cur = cur.next;
                return v;
            }
        };
    }

    private static final class Node<E> {       // static nested
        E value;
        Node<E> next;
        Node(E v, Node<E> n) { value = v; next = n; }
    }
}
```

(Yes, the iterator is an anonymous class — non-functional-interface
subclassing is still the right tool. Note that this is a good modern use
case.)

## Part E — Driver

`src/com/example/workflow/Main.java`:
```java
package com.example.workflow;

import java.util.EnumSet;

public class Main {
    public static void main(String[] args) {
        // Operation
        for (Operation op : Operation.values()) {
            System.out.println("3 " + op.symbol() + " 4 = " + op.apply(3, 4));
        }

        // Direction
        Direction d = Direction.NORTH;
        System.out.println(d + " -> left = " + d.left() + " | right = " + d.right() + " | opposite = " + d.opposite());

        // EnumSet
        EnumSet<Day> weekend = EnumSet.of(Day.SAT, Day.SUN);
        System.out.println("weekend size: " + weekend.size());

        // SimpleLinkedList
        var list = new SimpleLinkedList<String>();
        for (String s : "the quick brown fox".split(" ")) list.add(s);
        for (String s : list) System.out.println(s);
    }

    enum Day { MON, TUE, WED, THU, FRI, SAT, SUN }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.workflow.Main
```

Expected:
```
3 + 4 = 7
3 - 4 = -1
3 * 4 = 12
3 / 4 = 0
NORTH -> left = WEST | right = EAST | opposite = SOUTH
weekend size: 2
the
quick
brown
fox
```

## Part F — Lambda instead of anonymous class for `Comparator`

If you ever need to *sort* `SimpleLinkedList`'s elements, write a
`sort(Comparator)` method that uses a lambda:

```java
public void sort(Comparator<? super E> cmp) {
    // copy to array, sort, rebuild
    @SuppressWarnings("unchecked")
    E[] arr = (E[]) new Object[size];
    Node<E> cur = head; int i = 0;
    while (cur != null) { arr[i++] = cur.value; cur = cur.next; }
    java.util.Arrays.sort(arr, cmp);
    head = null; size = 0;
    for (E e : arr) add(e);
}
```

Use it:
```java
var ints = new SimpleLinkedList<Integer>();
for (int x : new int[]{3, 1, 4, 1, 5, 9}) ints.add(x);
ints.sort(Integer::compare);
```

Notice the difference: the iterator in `SimpleLinkedList` is *not* a
lambda because `Iterator` is a non-functional interface (it has two
abstract methods: `hasNext` and `next`). The comparator *is* a lambda
because `Comparator` is a `@FunctionalInterface`.

## What you learned

- Java enums can have fields, methods, and per-constant behaviour.
- `EnumSet` and `EnumMap` are O(1) and tiny — use them for sets and maps
  of enum values.
- Static nested classes are package-private implementation details.
- Inner classes (non-static) are rare; prefer lambdas.
- Anonymous classes are still needed for non-functional-interface
  subclassing.

➡️ **[challenge.md](./challenge.md)** then [Module 10](../10-annotations-reflection-modern/).
