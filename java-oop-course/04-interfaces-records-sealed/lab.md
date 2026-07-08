# Lab 04 — A Sealed `Payment` Hierarchy

**You'll:** build a small sum type with a `sealed` interface, several
`record` variants, and pattern-matching `switch` to render them. ⏱️ ~50 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop04 && cd ~/dev/oop04
mkdir -p src/com/example/payments
```

## Part B — The sealed interface and the records

`src/com/example/payments/Payment.java`:
```java
package com.example.payments;

public sealed interface Payment
        permits CardPayment, CashPayment, BankTransfer, ZeroPayment {

    long amountCents();
    String currency();

    default String description() {
        return "%s %.2f %s".formatted(kind(), amountCents() / 100.0, currency());
    }
    String kind();
}
```

`src/com/example/payments/CardPayment.java`:
```java
package com.example.payments;

public record CardPayment(long amountCents, String currency, String last4) implements Payment {
    public CardPayment {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (currency == null || currency.isBlank()) throw new IllegalArgumentException("currency required");
        if (last4 == null || last4.length() != 4)       throw new IllegalArgumentException("last4 required");
    }
    @Override public String kind() { return "card"; }
}
```

`src/com/example/payments/CashPayment.java`:
```java
package com.example.payments;

public record CashPayment(long amountCents, String currency) implements Payment {
    public CashPayment {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (currency == null) throw new IllegalArgumentException("currency required");
    }
    @Override public String kind() { return "cash"; }
}
```

`src/com/example/payments/BankTransfer.java`:
```java
package com.example.payments;

public record BankTransfer(long amountCents, String currency, String from) implements Payment {
    public BankTransfer {
        if (amountCents <= 0) throw new IllegalArgumentException("amount must be > 0");
        if (currency == null) throw new IllegalArgumentException("currency required");
        if (from == null || from.isBlank()) throw new IllegalArgumentException("from required");
    }
    @Override public String kind() { return "transfer"; }
}
```

`src/com/example/payments/ZeroPayment.java`:
```java
package com.example.payments;

public record ZeroPayment(String currency) implements Payment {
    public ZeroPayment {
        if (currency == null) throw new IllegalArgumentException("currency required");
    }
    @Override public long amountCents() { return 0; }
    @Override public String kind()      { return "zero"; }
}
```

## Part C — Driver

`src/com/example/payments/Main.java`:
```java
package com.example.payments;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<Payment> ledger = List.of(
            new CardPayment(12_99, "USD", "4242"),
            new CashPayment(5_00, "USD"),
            new BankTransfer(200_00, "USD", "acct-1234"),
            new ZeroPayment("USD")
        );

        for (Payment p : ledger) {
            System.out.println(render(p));
        }

        // Compile-time exhaustive switch — try adding a new record to
        // Payment and this switch will stop compiling.
    }

    public static String render(Payment p) {
        return switch (p) {
            case CardPayment c    -> "card    $" + (c.amountCents() / 100.0);
            case CashPayment      -> "cash    $" + (p.amountCents() / 100.0);
            case BankTransfer b   -> "xfer    $" + (b.amountCents() / 100.0) + " from " + b.from();
            case ZeroPayment      -> "zero";
        };
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.payments.Main
```

Expected:
```
card    $12.99
cash    $5.0
xfer    $200.0 from acct-1234
zero
```

✅ Notice the `switch` needs no `default` — the compiler can prove that
`Payment` is one of the four cases listed.

## Part D — Break the exhaustiveness check

Add a new `record CryptoPayment(...) implements Payment { ... }` to the
hierarchy. **Don't** update the `permits` list. Compile: you should get
`sealed interface permits clause` error. Restore the permits list, but
**don't** update `render`. Compile: you should get a "switch is not
exhaustive" error. This is the type system catching the gap for you.

## Part E — Add a guarded pattern

Change the `case CardPayment` to require a minimum amount:

```java
case CardPayment c when c.amountCents() >= 100_00 ->
        "big card  $" + (c.amountCents() / 100.0) + " ending " + c.last4();
case CardPayment c ->
        "small card $" + (c.amountCents() / 100.0) + " ending " + c.last4();
```

The first case matches a "big" card; the second matches any other card.
The compiler still considers the whole `CardPayment` arm covered.

## What you learned

- Interfaces are pure contracts (with optional `default` logic).
- Records give you immutable data classes in a single line — and the
  compact constructor is the validation spot.
- Sealed interfaces enumerate the permitted subtypes. The compiler
  enforces closure.
- A `switch` over a sealed type can be exhaustive — no `default` needed.
- Pattern matching (`instanceof` and `switch`) collapses the two-step
  cast into one.

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-generics/).
