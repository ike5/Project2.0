# Module 02 — OOP Foundations

**Goal:** understand Java's class model — fields, constructors, methods,
encapsulation, immutability, `this`, `static`, and packages. Build the first
class in the capstone app.

⏱️ ~2 h · 🎯 Prereq: Module 01.

---

## 1. The class is the unit of OOP

```java
package com.example.bank;

public final class BankAccount {                  // 'final' = cannot be subclassed

    // ---------- 1. Static (class-level) fields ----------
    private static int nextAccountNumber = 1_000;

    // ---------- 2. Instance fields (private, final wherever possible) ----------
    private final long accountNumber;
    private final String owner;
    private long balanceCents;                     // not final: this mutates

    // ---------- 3. Constructor ----------
    public BankAccount(String owner, long openingBalanceCents) {
        this.accountNumber = nextAccountNumber++;
        this.owner = Objects.requireNonNull(owner, "owner");
        if (openingBalanceCents < 0) {
            throw new IllegalArgumentException("opening balance must be >= 0");
        }
        this.balanceCents = openingBalanceCents;
    }

    // ---------- 4. Accessors ----------
    public long accountNumber()  { return accountNumber; }
    public String owner()        { return owner; }
    public long balanceCents()   { return balanceCents; }

    // ---------- 5. Behaviour ----------
    public void deposit(long amountCents) {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        balanceCents += amountCents;
    }

    public void withdraw(long amountCents) {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (amountCents > balanceCents) throw new IllegalStateException("insufficient funds");
        balanceCents -= amountCents;
    }

    @Override
    public String toString() {
        return "BankAccount[%d owner=%s balance=%.2f]"
                .formatted(accountNumber, owner, balanceCents / 100.0);
    }
}
```

This class is the template for every well-designed Java class:
**private fields, constructor that enforces invariants, accessor methods,
behaviour that maintains invariants, `toString` for debugging.**

## 2. `this` — a reference to the current object

`this` resolves ambiguity between fields and parameters:
```java
public BankAccount(String owner, long openingBalanceCents) {
    this.owner = owner;        // left: field; right: parameter
}
```
You can also pass the current object to other code (`otherMethod(this)`), or
return it for chaining.

## 3. `static` — class-level, not instance-level

A `static` field belongs to the class, not any object. One copy per class,
shared by all instances:
```java
private static int nextAccountNumber = 1_000;  // one counter for the whole class
```

A `static` method has no `this`. It can be called as `BankAccount.format(...)`
without an instance:
```java
public static String format(long cents) { return "$%.2f".formatted(cents / 100.0); }
```

A `static` initialiser block runs once, when the class is loaded:
```java
private static final Map<String, String> LABELS = new HashMap<>();
static { LABELS.put("USD", "US Dollar"); LABELS.put("EUR", "Euro"); }
```

## 4. Encapsulation — the most important OOP principle in practice

> **Hide the data. Expose the behaviour.**

The reason: invariants. An object that hands out its mutable internals
cannot guarantee they're still valid next time you look. Encapsulation
means:
- Fields are `private`.
- The class is `final` if no subclassing is intended.
- Mutators validate before changing state.
- Collections are *defensively copied* on input and output.

```java
public final class ShoppingCart {
    private final List<Item> items;
    public ShoppingCart(List<Item> initial) {
        this.items = new ArrayList<>(initial);   // defensive copy of the input
    }
    public List<Item> items() {
        return List.copyOf(items);               // defensive copy of the output
    }
    public void add(Item i) { items.add(i); }
}
```

If you pass a `List` straight through, a caller can do
`cart.items().clear()` and silently break the cart. Always copy.

## 5. Immutability — the strongest form of encapsulation

An **immutable object** can't change after construction. The benefits:
- **Thread-safe by construction.** Share freely across threads.
- **Hashable key** without surprises (`Map.of` and `Set.of` only accept
  immutable entries).
- **Easier to reason about.** You don't have to track all the places that
  might change the value.

A truly immutable Java type:
- Class is `final` (or all constructors are private and there's a static
  factory).
- All fields are `private final`.
- No mutator methods.
- Defensive copies of mutable inputs/outputs.
- No subclass can break the contract — hence `final`.

```java
public record Money(long cents, Currency currency) {
    public Money {
        Objects.requireNonNull(currency, "currency");
        if (cents < 0) throw new IllegalArgumentException("cents must be >= 0");
    }
    public Money add(Money other) {
        if (!currency.equals(other.currency)) {
            throw new IllegalArgumentException("currency mismatch");
        }
        return new Money(cents + other.cents, currency);
    }
}
```

`record` (covered properly in Module 04) gives you an immutable data class
in one line. Prefer it for value-like types.

## 6. Packages — Java's namespace mechanism

A package is a directory + a name. The directory layout must match:
```
src/com/example/bank/BankAccount.java
                ^^^^^^^^^^^^^^^^^^^^
                package declaration
```

To use a type from another package, `import` it:
```java
import java.util.Objects;
import java.util.List;
import com.example.bank.BankAccount;
```

**Package-private** (no modifier) means "visible to types in the *same*
package only." This is the right default for everything that isn't part of
the public API:

```java
public class Bank {                          // public API
    public BankAccount openAccount(String name) { /* ... */ }
    PackageLedger ledger() {                 // package-private implementation detail
        return new PackageLedger();
    }
    class PackageLedger { /* ... */ }
}
```

Same-package tests can use the package-private class. Outside callers cannot.
This is the cleanest way to keep tests white-box without exposing internals.

## 7. `static` factory methods — preferred over public constructors

A *static factory* is a static method that returns an instance. It has
advantages over a public constructor:
- It can have a name (`of`, `from`, `parse`, `random`).
- It can return a subtype, including one that didn't exist when the
  factory was written.
- It can cache and reuse instances (`Boolean.valueOf`).
- It can do precondition validation that reads naturally.

```java
public static BankAccount open(String owner) {
    return new BankAccount(owner, 0L);
}

public static BankAccount openWithDeposit(String owner, long cents) {
    return new BankAccount(owner, cents);
}
```

`BankAccount.open("Ada")` reads better than `new BankAccount("Ada", 0)`.

## 8. Object — the root of every class

Every class in Java extends `Object` (whether you say so or not). `Object`
defines:
- `toString()` — used by debuggers, loggers, `String.valueOf`. **Override
  it.** Default is `"com.example.Foo@1f3e02a"` — useless.
- `equals(Object o)` and `hashCode()` — used by `HashMap`, `HashSet`,
  `List.contains`, `assertEquals`, etc. **Override them together.**
- `getClass()` — returns the runtime class. Used in `instanceof` (now
  pattern matching).
- `clone()`, `wait()`, `notify()`, `notifyAll()` — legacy concurrency.
  Avoid.

```java
@Override
public boolean equals(Object o) {
    return o instanceof BankAccount other
        && accountNumber == other.accountNumber;       // accounts equal iff same number
}

@Override
public int hashCode() {
    return Objects.hash(accountNumber);
}
```

The rule: if `a.equals(b)`, then `a.hashCode() == b.hashCode()`. The
converse is not required. Many types have many objects that hash to the
same value; that's fine.

## 9. Layout — a checklist

A class header should read in this order:
1. Static fields (`public static final` constants first, then `private static`).
2. Instance fields (`private final` first, then `private` mutable).
3. Constructors.
4. Static factory methods.
5. Accessors.
6. Other instance methods.
7. `Object` overrides (`equals`, `hashCode`, `toString`).
8. `private` helpers at the bottom.

---

## Do the lab

Build a `BankAccount` class in `com.example.bank` and a tiny test driver.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

class · object / instance · field · method · constructor · `this` · `static` ·
encapsulation · immutability · `final` · `record` (preview) · package ·
package-private · static factory · `Object` · `equals`/`hashCode`/`toString`

**Next →** [Module 03: Inheritance & Polymorphism](../03-inheritance-polymorphism/)
