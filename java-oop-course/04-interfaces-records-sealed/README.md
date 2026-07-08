# Module 04 — Interfaces, Records & Sealed Types

**Goal:** master Java's three modern type-shaping tools: **interfaces** (a
contract), **records** (an immutable data class in one line), and **sealed
types** (a closed, exhaustively-checked hierarchy). All three combine to
produce the *sum type* — one of the most useful ideas in modern Java.

⏱️ ~3 h · 🎯 Prereq: Module 03.

---

## 1. Interfaces — pure contracts

An interface is a list of method signatures that any implementing class
must provide. Before Java 8, interfaces were *only* abstract methods; now
they can also have `default` and `static` methods.

```java
public interface Payment {
    long amountCents();           // abstract: implementor must provide
    String currency();

    default String description() {        // default: implementor gets it for free
        return "%d %s".formatted(amountCents(), currency());
    }

    static Payment zero(String currency) { // static: helper on the interface itself
        return new ZeroPayment(currency);
    }
}
```

A class `implements` one or more interfaces:
```java
public final class CardPayment implements Payment {
    private final long cents;
    private final String currency;
    private final String last4;
    public CardPayment(long cents, String currency, String last4) {
        this.cents = cents;
        this.currency = currency;
        this.last4 = last4;
    }
    @Override public long amountCents() { return cents; }
    @Override public String currency()   { return currency; }
    public String last4()                { return last4; }
}
```

A class can implement **any number of interfaces**:
```java
public final class StoredCard implements Payment, Serializable { /* ... */ }
```

## 2. `default` methods — interface evolution

`default` methods let you add a method to an interface without breaking
implementers. They became necessary in Java 8 because `Collection` needed
new methods (`stream`, etc.) without breaking every custom `Collection`
ever written.

```java
default String maskedCard() { return "**** **** **** " + last4(); }
```
The implementer inherits this method; if they want different behaviour,
they can override it.

Watch out for the **diamond problem**: if two interfaces both `default`
the same method, the implementing class must override the conflict.

## 3. `private` and `static` interface methods (Java 9+)

For shared logic across `default` methods, use `private` (file-internal)
and `static` (callable as `Interface.helper(...)`):

```java
public interface Payment {
    default String description() { return formatCents(amountCents()) + " " + currency(); }
    private String formatCents(long cents) { return "$" + (cents / 100.0); }    // helper
}
```

## 4. `record` — the data class, condensed

A `record` declares a class whose **only state is its fields**, in one
line. The compiler generates:
- a constructor (`RecordField` params, in declaration order),
- accessors named after each field (no `get` prefix),
- `equals`, `hashCode`, and `toString`.

```java
public record Point(int x, int y) { }
```

This single line is equivalent to:
```java
public final class Point {
    private final int x, y;
    public Point(int x, int y) { this.x = x; this.y = y; }
    public int x() { return x; }
    public int y() { return y; }
    @Override public String toString()  { return "Point[x=" + x + ", y=" + y + "]"; }
    @Override public boolean equals(Object o) {
        return o instanceof Point p && p.x == x && p.y == y;
    }
    @Override public int hashCode() { return Objects.hash(x, y); }
}
```

You can add methods, override accessors, and **validate inputs in a
compact constructor**:

```java
public record Money(long cents, Currency currency) {
    public Money {                                          // compact constructor
        Objects.requireNonNull(currency, "currency");
        if (cents < 0) throw new IllegalArgumentException("cents must be >= 0");
    }
    public Money add(Money other) {
        if (!currency.equals(other.currency)) throw new IllegalArgumentException("currency mismatch");
        return new Money(cents + other.cents, currency);
    }
}
```

Records **are implicitly `final`** and their fields are `private final`.
You cannot extend a record or add instance fields.

## 5. When to use `record` vs. `class`

**Use a record** when:
- The type is "a bundle of immutable values" with **no meaningful identity**
  beyond those values.
- Equality is structural (two records with the same fields are equal).
- The class is short and rarely overridden.

**Use a class** when:
- The type has state that changes over time.
- It has invariants more complex than per-field validation.
- Equality is *identity-based* (two `BankAccount` with the same number are
  the same account, but two `Money` with the same amount and currency are
  interchangeable).
- You need inheritance or a non-trivial lifecycle.

The library code is full of records: HTTP request lines, log entries,
database row DTOs, money, coordinates, time ranges. Use them.

## 6. Sealed types — closed hierarchies

A `sealed` interface or class lists the types that are allowed to extend
it. The compiler then knows the hierarchy is **closed** and can check
`switch` exhaustiveness.

```java
public sealed interface Payment
        permits CardPayment, CashPayment, BankTransfer, ZeroPayment {

    long amountCents();
    String currency();
}

public final class CardPayment    implements Payment { /* ... */ }
public final class CashPayment    implements Payment { /* ... */ }
public final class BankTransfer   implements Payment { /* ... */ }
public final class ZeroPayment    implements Payment { /* ... */ }
```

Two restrictions:
- Every permitted subtype must be in the same module (or, if you prefer,
  you can have them in the same package with no `permits` clause).
- Each permitted subtype must be `final`, `sealed`, or `non-sealed`. A
  `non-sealed` subtype can be extended further (use sparingly).

## 7. Pattern matching for `switch` on sealed types

The big payoff: the compiler can verify you handled every case.

```java
public static String describe(Payment p) {
    return switch (p) {
        case CardPayment c  -> "card " + c.last4();
        case CashPayment    -> "cash";
        case BankTransfer b -> "transfer from " + b.from();
        case ZeroPayment    -> "zero";
    };     // no default needed — sealed hierarchy is exhaustive
}
```

If you add a new subtype to the `permits` list without updating this
`switch`, **the code stops compiling**. The compiler is your exhaustive
checker.

You can also use **guarded patterns**:
```java
case CardPayment c when c.amountCents() > 10_000_00 -> "big card " + c.last4();
```

## 8. Pattern matching for `instanceof`

The classic two-step cast:
```java
if (obj instanceof String) {
    String s = (String) obj;
    System.out.println(s.length());
}
```

Becomes a one-step pattern:
```java
if (obj instanceof String s) {
    System.out.println(s.length());
}
```

The variable `s` is in scope only in the truthy branch and is guaranteed
non-null. Combine with `&&` and other conditions:
```java
if (obj instanceof String s && s.length() > 3) {
    System.out.println(s.toUpperCase());
}
```

## 9. A complete example

```java
public sealed interface Result<V> permits Success, Failure {
    static <V> Result<V> of(V value) { return new Success<>(value); }
    static <V> Result<V> error(String message) { return new Failure<>(message); }
}

public record Success<V>(V value) implements Result<V> { }
public record Failure<V>(String message) implements Result<V> { }

public static String render(Result<Integer> r) {
    return switch (r) {
        case Success<Integer> s -> "ok: " + s.value();
        case Failure<Integer> f -> "error: " + f.message();
    };
}
```

This is the **sum type** pattern: a closed set of variants, one of which
is held at a time. In modern Java, it replaces a lot of `null` returns
and checked exceptions at API boundaries.

## 10. The OOP decision tree

| If your type is… | Use… |
|------------------|------|
| Immutable data, equality is structural, no behaviour beyond accessors | `record` |
| A closed set of variants | `sealed` interface + `record` or `final` permits list |
| A capability that many unrelated types will implement | interface with `default` methods |
| A partial implementation that subclasses share | `abstract class` |
| A thing with state, identity, and complex invariants | `final class` |
| A class whose main job is to *act* on other things | `final class` with static methods (utility) |

---

## Do the lab

Build a small `Payment` hierarchy with `sealed` + `record` and exercise
exhaustive pattern matching. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

interface · `default` method · `static` method (interface) · `record` ·
compact constructor · `sealed` · `permits` · `non-sealed` · exhaustive
`switch` · pattern matching for `instanceof` · pattern matching for `switch` ·
guarded pattern (`when`) · sum type

**Next →** [Module 05: Generics & Type Parameters](../05-generics/)
