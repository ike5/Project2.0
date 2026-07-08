# Lab 07 — Lambdas & Streams Hands-On

**You'll:** build a tiny `Orders` domain and write several stream
pipelines that read like the problem statements. ⏱️ ~55 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop07 && cd ~/dev/oop07
mkdir -p src/com/example/orders
```

## Part B — The domain

`src/com/example/orders/Order.java`:
```java
package com.example.orders;

import java.time.Instant;
import java.util.List;

public record Order(long id, String customer, List<String> items, long totalCents, Instant placedAt) {
    public Order {
        items = List.copyOf(items);
    }
}
```

`src/com/example/orders/LineItem.java`:
```java
package com.example.orders;

public record LineItem(String sku, int quantity, long unitPriceCents) {
    public long lineTotal() { return (long) quantity * unitPriceCents; }
}
```

## Part C — A reporting service

`src/com/example/orders/Reporting.java`:
```java
package com.example.orders;

import java.time.Instant;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

public final class Reporting {
    private Reporting() {}

    /** All orders over the threshold. */
    public static List<Order> largeOrders(List<Order> orders, long thresholdCents) {
        return orders.stream()
                .filter(o -> o.totalCents() >= thresholdCents)
                .sorted(Comparator.comparing(Order::totalCents).reversed())
                .toList();
    }

    /** Total revenue from a list of orders. */
    public static long totalRevenue(List<Order> orders) {
        return orders.stream().mapToLong(Order::totalCents).sum();
    }

    /** Revenue grouped by customer. */
    public static Map<String, Long> revenueByCustomer(List<Order> orders) {
        return orders.stream().collect(Collectors.groupingBy(
                Order::customer,
                Collectors.summingLong(Order::totalCents)));
    }

    /** The most recent order, if any. */
    public static Optional<Order> mostRecent(List<Order> orders) {
        return orders.stream().max(Comparator.comparing(Order::placedAt));
    }

    /** Top-3 customers by total spend, descending. */
    public static List<Map.Entry<String, Long>> topCustomersBySpend(List<Order> orders, int n) {
        return revenueByCustomer(orders).entrySet().stream()
                .sorted(Map.Entry.<String, Long>comparingByValue().reversed())
                .limit(n)
                .toList();
    }

    /** Orders placed in the last `seconds` seconds. */
    public static List<Order> recentOrders(List<Order> orders, long seconds) {
        Instant cutoff = Instant.now().minusSeconds(seconds);
        return orders.stream()
                .filter(o -> o.placedAt().isAfter(cutoff))
                .toList();
    }
}
```

## Part D — Driver

`src/com/example/orders/Main.java`:
```java
package com.example.orders;

import java.time.Instant;
import java.util.List;
import java.util.Map;

public class Main {
    public static void main(String[] args) {
        var now = Instant.now();
        var orders = List.of(
            new Order(1, "Ada",    List.of("a", "b"),  1200, now.minusSeconds(60)),
            new Order(2, "Grace",  List.of("c"),       500,  now.minusSeconds(30)),
            new Order(3, "Ada",    List.of("d", "e"),  4500, now.minusSeconds(10)),
            new Order(4, "Alan",   List.of("f"),      20000, now.minusSeconds(120))
        );

        System.out.println("large (>=$10): " + Reporting.largeOrders(orders, 1000));
        System.out.println("revenue: " + Reporting.totalRevenue(orders));
        System.out.println("by customer: " + Reporting.revenueByCustomer(orders));
        System.out.println("most recent: " + Reporting.mostRecent(orders).orElseThrow());
        System.out.println("top 2: " + Reporting.topCustomersBySpend(orders, 2));
        System.out.println("recent (60s): " + Reporting.recentOrders(orders, 60).size());
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.orders.Main
```

Expected (revenue numbers are deterministic; timing may vary):
```
large (>=$10): [Order[id=4, customer=Alan, totalCents=20000], Order[id=3, customer=Ada, totalCents=4500], Order[id=1, customer=Ada, totalCents=1200]]
revenue: 26200
by customer: {Grace=500, Ada=5700, Alan=20000}
most recent: Order[id=3, customer=Ada, totalCents=4500, ...]
top 2: [Alan=20000, Ada=5700]
recent (60s): 2
```

✅ Every query in `Reporting` is a one-method stream pipeline. Notice how
the data flow is clear at a glance.

## Part E — Method references vs. lambdas

In `Reporting.revenueByCustomer`, we wrote `Order::totalCents` for a
`long` extractor. That works because `Collectors.summingLong` takes a
`ToLongFunction<Order>`, and a method reference to a `long`-returning
method is auto-adapted.

Try the same with `Collectors.summingInt(Order::id)` — won't compile,
because `Order::id` returns `long`, not `int`. The compiler points you
at the right `summingX` overload for the type you have.

## Part F — Side-effecting with `peek` (debugging only)

Add a temporary line to `Reporting.largeOrders` to see the elements as
they flow through:
```java
.peek(o -> System.out.println("peek: " + o))
```
This is for **debugging** only. Don't use `peek` to mutate state.

## What you learned

- `@FunctionalInterface` is a single-abstract-method interface; lambdas
  target it.
- Method references are shorthand for lambdas; use them when they're
  shorter and equally clear.
- Streams are lazy pipelines: intermediate operations return a stream;
  a terminal op runs everything.
- `Collectors` is the toolbox for "reduce a stream to a value": grouping,
  partitioning, summing, joining.
- `Optional` is for return types; never for fields or parameters.
- Primitive streams (`IntStream`, `LongStream`, `DoubleStream`) avoid
  boxing and have built-in `sum`/`average`/`min`/`max`.

➡️ **[challenge.md](./challenge.md)** then [Module 08](../08-exceptions-optional/).
