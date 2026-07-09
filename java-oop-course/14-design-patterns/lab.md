# Lab 14 — Design Patterns Hands-On

**You'll:** build a small text-decoration library that uses Strategy,
Decorator, and Builder together. ⏱️ ~50 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop14 && cd ~/dev/oop14
mkdir -p src/com/example/patterns
```

## Part B — Strategy: a `PricingStrategy`

`src/com/example/patterns/PricingStrategy.java`:
```java
package com.example.patterns;

@FunctionalInterface
public interface PricingStrategy {
    long price(long baseCents);
}
```

`src/com/example/patterns/Pricing.java`:
```java
package com.example.patterns;

public final class Pricing {
    public static final PricingStrategy REGULAR = base -> base;
    public static final PricingStrategy PREMIUM = base -> Math.round(base * 0.85);
    public static final PricingStrategy VIP     = base -> Math.round(base * 0.50);

    private Pricing() {}
}
```

## Part C — Builder: an `Order`

`src/com/example/patterns/Order.java`:
```java
package com.example.patterns;

import java.util.Objects;

public record Order(long id, String customer, long baseCents, long finalCents) {
    public Order {
        if (id <= 0) throw new IllegalArgumentException("id > 0");
        Objects.requireNonNull(customer, "customer");
        if (baseCents < 0) throw new IllegalArgumentException("baseCents >= 0");
    }

    public Order apply(PricingStrategy strategy) {
        return new Order(id, customer, baseCents, strategy.price(baseCents));
    }

    public static Builder builder() { return new Builder(); }

    public static final class Builder {
        private long id;
        private String customer;
        private long baseCents;
        public Builder id(long id)              { this.id = id; return this; }
        public Builder customer(String c)      { this.customer = c; return this; }
        public Builder baseCents(long b)       { this.baseCents = b; return this; }
        public Order build()                    { return new Order(id, customer, baseCents, baseCents); }
    }
}
```

## Part D — Decorator: a `Text` builder

`src/com/example/patterns/Text.java`:
```java
package com.example.patterns;

@FunctionalInterface
public interface Text {
    String render();

    static Text of(String s) { return () -> s; }

    default Text bold()      { return () -> "<b>" + render() + "</b>"; }
    default Text italic()    { return () -> "<i>" + render() + "</i>"; }
    default Text underline() { return () -> "<u>" + render() + "</u>"; }
}
```

## Part E — Observer: a tiny event bus

`src/com/example/patterns/EventBus.java`:
```java
package com.example.patterns;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

public final class EventBus<T> {
    private final List<Consumer<T>> listeners = new CopyOnWriteArrayList<>();

    public AutoCloseable subscribe(Consumer<T> listener) {
        listeners.add(listener);
        return () -> listeners.remove(listener);
    }

    public void publish(T event) {
        for (var l : listeners) l.accept(event);
    }
}
```

## Part F — Driver

`src/com/example/patterns/Main.java`:
```java
package com.example.patterns;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        // Strategy
        var order = Order.builder()
                .id(1).customer("Ada").baseCents(10_00)
                .build()
                .apply(Pricing.PREMIUM);
        System.out.println("order: " + order + " (final " + order.finalCents() + " cents)");

        // Decorator
        Text text = Text.of("Hello, Java").bold().italic();
        System.out.println("text: " + text.render());

        // Observer
        var bus = new EventBus<String>();
        Runnable s1 = bus.subscribe(msg -> System.out.println("sub1: " + msg));
        Runnable s2 = bus.subscribe(msg -> System.out.println("sub2: " + msg));
        bus.publish("event 1");
        bus.publish("event 2");
        s1.run();   // unsubscribe s1
        s2.run();   // unsubscribe s2
        bus.publish("(no listeners)");

        // Factory (a static factory on a record)
        List<Order> bulk = List.of(
                Order.builder().id(2).customer("Grace").baseCents(5_00).build(),
                Order.builder().id(3).customer("Alan").baseCents(20_00).build()
        );
        System.out.println("bulk: " + bulk);
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.patterns.Main
```

Expected:
```
order: Order[id=1, customer=Ada, baseCents=1000, finalCents=850] (final 850 cents)
text: <i><b>Hello, Java</b></i>
sub1: event 1
sub2: event 1
sub1: event 2
sub2: event 2
bulk: [Order[...], Order[...]]
```

✅ Each pattern is short — a single file. The Decorator is *just*
default methods on a `@FunctionalInterface`. The Strategy is a
functional interface and three constants. The Builder is a single
nested `Builder` class. The Observer is a `List<Consumer<T>>` plus
subscribe/unsubscribe.

## What you learned

- Patterns are smaller in modern Java than the GoF book suggests.
- Functional interfaces replace class hierarchies for Strategy and
  Observer.
- Default methods replace class hierarchies for Decorator.
- Records + builders replace telescoping constructors.
- The Singleton pattern is now one line in an `enum`.

➡️ **[challenge.md](./challenge.md)** then [Module 15](../15-capstone-library/).
