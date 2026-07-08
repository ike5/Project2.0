# Lab 02 — A `BankAccount` Class

**You'll:** design and build a single class, exercise encapsulation and
immutability, and see what happens when invariants aren't enforced.

⏱️ ~45 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop02 && cd ~/dev/oop02
mkdir -p src/com/example/bank
```

## Part B — Build `BankAccount`

Write `src/com/example/bank/BankAccount.java` from the README's reference.
Key things to verify while typing:

- `private final` for the account number and owner (immutable).
- `private long balanceCents` is *mutable* (the balance changes).
- The constructor validates `openingBalanceCents >= 0` and rejects
  `null` owner with `Objects.requireNonNull`.
- `deposit` and `withdraw` both validate the amount.
- `withdraw` throws `IllegalStateException` if funds are insufficient.
- `toString` formats the balance in dollars (cents / 100.0).
- `equals` and `hashCode` are based on the account number (which is
  unique).

Compile:
```bash
javac -d out $(find src -name '*.java')
```

## Part C — A driver

`src/com/example/bank/Main.java`:
```java
package com.example.bank;

public class Main {
    public static void main(String[] args) {
        var a = BankAccount.open("Ada");
        a.deposit(10_00);
        a.withdraw(3_50);
        System.out.println(a);                    // balance $6.50

        var b = BankAccount.open("Grace");
        b.deposit(50_00);
        System.out.println(b);

        // invariant violations
        try { a.withdraw(999_00); }
        catch (IllegalStateException e) { System.out.println("rejected: " + e.getMessage()); }

        try { BankAccount.open(null); }
        catch (NullPointerException e) { System.out.println("rejected: " + e.getMessage()); }

        // equality
        var a2 = BankAccount.open("Ada");
        System.out.println("a == a2: " + a.equals(a2));     // false (different account numbers)
        System.out.println("a == a : " + a.equals(a));      // true
    }
}
```

Run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.bank.Main
```

Expected:
```
BankAccount[1000 owner=Ada balance=6.50]
BankAccount[1001 owner=Grace balance=50.00]
rejected: insufficient funds
rejected: owner
a == a2: false
a == a : true
```

✅ Confirm:
- The two accounts got *different* numbers (1000, 1001) — that's `static`
  `nextAccountNumber` working.
- Invariant violations are rejected, not silently accepted.
- Two accounts with the same owner are *not* equal (the number is the key).

## Part D — Demonstrate the encapsulation bug

Add a quick experiment to `Main.main` (or write a new class) to *prove* that
`private` actually hides state:

```java
import java.lang.reflect.Field;

public class EncapsulationHole {
    public static void main(String[] args) throws Exception {
        var a = BankAccount.open("Ada");
        Field f = BankAccount.class.getDeclaredField("owner");
        f.setAccessible(true);                    // bypasses the access check
        f.set(a, "Mallory");
        System.out.println(a);                    // shows owner = Mallory
    }
}
```

`javac EncapsulationHole.java && java EncapsulationHole` — the field *can*
be mutated via reflection, but only with a deliberate bypass. This is
exactly what `private` is meant to do: stop honest mistakes and casual
attacks, not stop a determined attacker with full JVM access.

## Part E — An immutable variant

Try writing `Money` as a record in `com.example.bank.Money`:
```java
package com.example.bank;

import java.util.Currency;
import java.util.Objects;

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
    public static Money usd(long cents) { return new Money(cents, Currency.getInstance("USD")); }
}
```

Notice: no setters, no defensive-copy code needed, the constructor
*is* the validator, and the record is automatically `final`.

---

## What you learned

- A class is private fields + validating constructor + accessors + behaviour.
- `static` is class-level state; `final` is "this can't change."
- Encapsulation means hiding state and copying collections in/out.
- `equals` and `hashCode` are paired; override them together.
- Records are the easy button for immutable data — but only when there's
  no behaviour beyond "operate on the fields."

➡️ **[challenge.md](./challenge.md)** then [Module 03](../03-inheritance-polymorphism/).
