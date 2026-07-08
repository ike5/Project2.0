# Module 09 — Enums, Nested & Inner Classes

**Goal:** use **rich enums** for finite state machines, **static nested
classes** for tightly-coupled helpers, and avoid the pitfalls of inner
classes and anonymous classes now that lambdas exist.

⏱️ ~2 h · 🎯 Prereq: Module 08.

---

## 1. Enums are not just constants

A Java `enum` is a class with a fixed, named set of instances. Each
constant is a `public static final` instance of the enum type, and
nothing else can be created.

```java
public enum Direction {
    NORTH, EAST, SOUTH, WEST;

    public Direction left() {
        return switch (this) {
            case NORTH -> WEST;
            case WEST  -> SOUTH;
            case SOUTH -> EAST;
            case EAST  -> NORTH;
        };
    }
    public Direction right() { return left().left().left(); }   // or 3x left()
    public Direction opposite() { return left().left(); }
}
```

You get:
- `values()` — array of all constants.
- `valueOf(String)` — constant by name (case-sensitive, throws).
- `name()`, `ordinal()` — the constant's name and declaration order.
- `EnumSet` and `EnumMap` for sets and maps of enum values (constant time,
  bit-vector backed).

## 2. Rich enums — fields, methods, per-constant behaviour

```java
public enum Operation {
    ADD("+")      { long apply(long a, long b) { return a + b; } },
    SUBTRACT("-") { long apply(long a, long b) { return a - b; } },
    MULTIPLY("*") { long apply(long a, long b) { return a * b; } },
    DIVIDE("/")   { long apply(long a, long b) { return a / b; } };

    private final String symbol;
    Operation(String symbol) { this.symbol = symbol; }
    abstract long apply(long a, long b);

    public String symbol() { return symbol; }
}
```

Each constant has its own `apply` method. This is the *constant-specific
method* idiom — it eliminates `switch` on enum value and keeps the
behaviour next to the constant.

## 3. Enums with state — finite state machines

```java
public enum ConnectionState {
    DISCONNECTED {
        @Override public ConnectionState onConnect() { return CONNECTED; }
        @Override public ConnectionState onDisconnect() { return this; }
    },
    CONNECTED {
        @Override public ConnectionState onConnect() { return this; }
        @Override public ConnectionState onDisconnect() { return DISCONNECTED; }
    };

    public abstract ConnectionState onConnect();
    public abstract ConnectionState onDisconnect();
}
```

The state machine becomes a type-checked transition table. Compare this
to a `switch` on a `String` — there's no possibility of a typo'd state.

## 4. Enums vs. sealed interfaces (Module 04)

Modern Java lets you express a finite set of variants as a
`sealed` interface with `record` permits. Use that when each variant
carries **different data**. Use an `enum` when each variant is *the same
shape* and the differences are *behaviour*.

```java
// Use enum: same shape, different behaviour.
public enum Color { RED, GREEN, BLUE }

// Use sealed: each variant carries its own fields.
public sealed interface Shape permits Circle, Rectangle, Triangle { ... }
public record Circle(double radius) implements Shape { ... }
```

## 5. Static nested classes

A class declared `static` inside another class. Behaves like a top-level
class for access purposes — no implicit reference to the enclosing
instance.

```java
public final class LinkedList<E> {
    // ...
    private static class Node<E> {           // static nested
        E value;
        Node<E> next;
        Node(E v, Node<E> n) { value = v; next = n; }
    }
}
```

Static nested classes are useful for **implementation details** that
are tightly coupled to the outer class but don't need its instance.

## 6. Inner classes (non-static)

A non-static nested class has an *implicit reference* to its enclosing
instance. They're a remnant of pre-lambda Java and have very few good
uses today.

```java
public class Outer {
    private final String name = "outer";

    public class Inner {                      // not 'static'
        public String describe() { return "from " + name; }    // captures outer's name
    }
}
```

Why this is rare:
- A `new Outer().new Inner()` has surprising construction syntax.
- The implicit `this$0` reference prevents GC of the outer instance
  while the inner one is alive.
- Lambdas do almost everything inner classes used to do, *and* don't
  keep the outer alive.

**Use them only** for:
- View objects (Swing's `MouseAdapter`, etc.).
- Adapter classes that genuinely need access to enclosing instance state.

## 7. Local classes

A class declared inside a method. Rare in modern code — prefer lambdas
or static nested classes.

```java
public void doIt() {
    class LocalHelper {
        int compute(int x) { return x * 2; }
    }
    new LocalHelper().compute(21);
}
```

## 8. Anonymous classes

A class declared and instantiated in a single expression:
```java
list.sort(new Comparator<String>() {
    @Override public int compare(String a, String b) { return a.length() - b.length(); }
});
```

In modern Java, **replace with a lambda**:
```java
list.sort((a, b) -> a.length() - b.length());
```

Anonymous classes are still used for non-functional-interface types
(e.g. subclassing a concrete class), but those are rare.

## 9. `EnumSet` and `EnumMap`

For a set or map whose key is an enum, the JDK provides O(1) and
extremely compact implementations:

```java
EnumSet<Permission> perms = EnumSet.of(Permission.READ, Permission.WRITE);
EnumMap<Day, Schedule> schedule = new EnumMap<>(Day.class);
schedule.put(Day.MON, new Schedule("deep work"));
```

Don't use `HashSet<Permission>` when `EnumSet` exists. The difference
in space and time is significant.

## 10. A worked example: `WorkflowStep`

```java
public enum WorkflowStep {
    PENDING {
        @Override public WorkflowStep approve() { return APPROVED; }
        @Override public WorkflowStep reject()  { return REJECTED; }
    },
    APPROVED {
        @Override public WorkflowStep approve() { return this; }   // already approved
        @Override public WorkflowStep reject()  { return REJECTED; }
    },
    REJECTED {
        @Override public WorkflowStep approve() { return this; }   // terminal
        @Override public WorkflowStep reject()  { return this; }   // terminal
    };

    public abstract WorkflowStep approve();
    public abstract WorkflowStep reject();
}
```

This is small, type-safe, and impossible to misuse. Compare to a `String`
workflow status: typos allowed, "what does 'partial' mean?" debates
forever.

---

## Do the lab

Build a rich `Operation` enum and exercise the constant-specific-method
idiom. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

enum · `values()` / `valueOf` · `name()` / `ordinal()` · constant-specific
method · rich enum · finite state machine · `EnumSet` · `EnumMap` ·
static nested class · inner class · local class · anonymous class ·
lambda replacement

**Next →** [Module 10: Annotations, Reflection & Modern Sugar](../10-annotations-reflection-modern/)
