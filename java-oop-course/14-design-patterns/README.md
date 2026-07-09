# Module 14 — Design Patterns in Modern Java

**Goal:** recognise and apply the most useful object-oriented design
patterns — and recognise when modern Java features (records, sealed
types, lambdas) have made the *old* implementations simpler or
unnecessary.

⏱️ ~3 h · 🎯 Prereq: Module 13.

---

## 1. Why patterns?

Patterns are *named solutions to recurring problems*. They give you a
vocabulary for talking about design and a starting point for
implementation. They're not laws — modern Java sometimes makes a
pattern unnecessary (see Singleton below).

## 2. Strategy

**Intent:** define a family of algorithms, encapsulate each, and make
them interchangeable.

**Modern Java form:** a `@FunctionalInterface` (or a sealed hierarchy)
passed as a constructor argument.

```java
@FunctionalInterface
public interface PricingStrategy {
    long price(long baseCents);
}

public final class Order {
    private final PricingStrategy pricing;
    public Order(PricingStrategy pricing) { this.pricing = pricing; }
    public long total(long base) { return pricing.price(base); }
}

var regular = new Order(base -> base);
var premium = new Order(base -> Math.round(base * 0.85));
var vip     = new Order(base -> Math.round(base * 0.50));
```

The pre-Java-8 form — a class hierarchy with `RegularPricing`,
`PremiumPricing`, etc. — is verbose. The lambda form is one line per
strategy and doesn't need new types.

## 3. Decorator

**Intent:** attach additional behaviour to an object dynamically.

**Modern Java form:** an interface with `default` methods, or a wrapper
class implementing the same interface.

```java
public interface Text {
    String render();
    default Text bold() { return () -> "<b>" + render() + "</b>"; }
    default Text italic() { return () -> "<i>" + render() + "</i>"; }
}

Text t = ((Text) () -> "Hello").bold().italic();
// "<i><b>Hello</b></i>"
```

The class-hierarchy form (`BoldText extends PlainText`) is heavy. The
default-method / lambda form is two lines per decoration.

## 4. Builder

**Intent:** construct complex objects step by step, with optional fields.

**Modern Java form:** a record's compact constructor + a static
`builder()` returning a private `Builder` class.

```java
public record ServerConfig(String host, int port, int maxConnections, Duration timeout) {
    public ServerConfig {
        Objects.requireNonNull(host, "host");
        if (port <= 0) throw new IllegalArgumentException("port > 0");
        // ... validate the rest
    }

    public static Builder builder() { return new Builder(); }

    public static final class Builder {
        private String host = "localhost";
        private int port = 8080;
        private int maxConnections = 100;
        private Duration timeout = Duration.ofSeconds(30);

        public Builder host(String h) { this.host = h; return this; }
        public Builder port(int p)    { this.port = p; return this; }
        public Builder maxConnections(int m) { this.maxConnections = m; return this; }
        public Builder timeout(Duration t) { this.timeout = t; return this; }

        public ServerConfig build() { return new ServerConfig(host, port, maxConnections, timeout); }
    }
}

var cfg = ServerConfig.builder()
        .host("example.com")
        .port(443)
        .maxConnections(50)
        .build();
```

A builder is the right choice when an object has 4+ optional fields, or
when the construction process is complex. For a one-field record, a
static factory (`ServerConfig.of(...)`) is enough.

## 5. Factory

**Intent:** encapsulate object construction in a method, so the caller
doesn't need to know the concrete type.

```java
public static Animal create(String kind) {
    return switch (kind) {
        case "dog"   -> new Dog();
        case "cat"   -> new Cat();
        case "duck"  -> new Duck();
        default      -> throw new IllegalArgumentException("unknown: " + kind);
    };
}
```

In modern Java, this is even cleaner with sealed types — the compiler
checks exhaustiveness. Combine with a record's canonical constructor for
"named constructor" semantics.

## 6. Observer

**Intent:** when one object changes state, notify all its dependents
automatically.

**Modern Java form:** a `Consumer<T>` field (a "listener") the
publisher invokes.

```java
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

var bus = new EventBus<String>();
var sub = bus.subscribe(msg -> System.out.println("got: " + msg));
bus.publish("hello");
sub.close();          // unsubscribe
bus.publish("...");
```

The "listener" is a single-method functional interface; the
`subscribe` method returns an `AutoCloseable` so the caller can
unsubscribe via `try (...)` or `close()`.

## 7. Adapter

**Intent:** convert one interface to another.

**Modern Java form:** a `Function<F, T>` or a tiny `Adapter` class.

```java
// Adapt a List<Integer> to an IntStream.
IntStream ints = list.stream().mapToInt(Integer::intValue);

// Adapt an old interface to a new one.
Function<OldEvent, NewEvent> adapt =
    old -> new NewEvent(old.id(), old.timestamp());
```

Adapters are everywhere; they're often one-liners in modern Java.

## 8. Singleton — the modern form

**Intent:** a class with exactly one instance.

**Modern Java form:** an `enum` with one constant, or a `record` with a
private static field.

```java
// The GoF-blessed form: a public final field.
public enum AppSettings {
    INSTANCE;
    private final Properties props = load();
    public String get(String key) { return props.getProperty(key); }
}

// Or with a record:
public record AppConfig(String env) {
    private static final AppConfig DEFAULT = new AppConfig("production");
    public static AppConfig get() { return DEFAULT; }
}
```

Pre-Java-5, singletons needed double-checked locking with `volatile`.
Modern Java has neither bug nor ceremony.

## 9. Composite

**Intent:** treat individual objects and compositions uniformly, often
as tree structures.

**Modern Java form:** a sealed interface with a recursive `record` for
branches and a `record` for leaves.

```java
public sealed interface JsonValue permits JsonObject, JsonArray, JsonString, JsonNumber, JsonBoolean, JsonNull {
    String render();
}
public record JsonString(String value) implements JsonValue { public String render() { return "\"" + value + "\""; } }
public record JsonNumber(double value) implements JsonValue { public String render() { return Double.toString(value); } }
public record JsonObject(Map<String, JsonValue> fields) implements JsonValue {
    public String render() {
        return "{" + fields.entrySet().stream()
                .map(e -> "\"" + e.getKey() + "\": " + e.getValue().render())
                .collect(Collectors.joining(", ")) + "}";
    }
}
// ... etc.
```

The sealed interface makes the type explicit; the records make
construction simple. A `switch (value)` over `JsonValue` is exhaustive
without a `default`.

## 10. Visitor (the modern version)

**Intent:** add new operations to a class hierarchy without modifying
the classes.

**Modern Java form:** pattern matching for `switch`.

```java
String describe(Shape s) {
    return switch (s) {
        case Circle c    -> "circle r=" + c.radius();
        case Rectangle r -> "rectangle " + r.width() + "x" + r.height();
        case Triangle t  -> "triangle";
    };
}
```

The pre-Java-21 Visitor pattern (an `accept(Visitor v)` method and a
`Visitor` interface) is obsolete for sealed hierarchies. Keep Visitor
for *open* hierarchies where you can't add a method to the type.

## 11. Iterator

**Intent:** traverse a collection without exposing its representation.

This pattern is so fundamental in Java that the `Iterable` interface
*is* the pattern. `for (var x : collection) { ... }` is sugar for
`for (Iterator<T> it = collection.iterator(); it.hasNext(); ) { var x =
it.next(); ... }`.

## 12. Façade

**Intent:** a single high-level interface to a set of subsystems.

```java
public final class Library {
    public static Result<Book, String> checkout(long bookId, long memberId) { /* ... */ }
    public static Result<Void, String> returnBook(long loanId) { /* ... */ }
    public static List<Book> search(String query) { /* ... */ }
}
```

The caller doesn't need to know about `BookRepository`,
`LoanRepository`, `MemberService`, etc. — only the façade.

## 13. Dependency Injection (preview)

**Intent:** provide an object's dependencies from outside, rather than
letting it construct them.

In modern Java (without a framework), you do it by hand:
```java
public final class CheckoutService {
    private final BookRepository books;
    private final LoanRepository loans;
    public CheckoutService(BookRepository books, LoanRepository loans) {
        this.books = books; this.loans = loans;
    }
    public Result<Loan, String> checkout(long bookId, long memberId) { /* ... */ }
}
```

The caller (often a `Main` or a test) constructs the repositories and
passes them in. This is the basis of Spring, Guice, and Dagger — but
for small programs, manual DI is fine.

## 14. The patterns *not* to reach for

- **Singleton-everywhere** — most "singletons" should just be
  parameters you pass around. The configuration object is a singleton;
  the formatter is not.
- **Factory-when-constructor-is-clear** — `new ArrayList<>()` is a
  factory. Don't hide it behind another factory.
- **Observer-when-a-`Consumer`-is-enough** — the pattern is a list of
  consumers. If you only have one, just take a `Consumer<T>` parameter.
- **Visitor-when-switch-is-exhaustive** — modern Java's `switch` is
  the visitor for sealed types.

## 15. A worked example — composing patterns

A small `OrderProcessor` uses:
- **Strategy** — a `PricingStrategy` parameter.
- **Builder** — for the `Order` itself.
- **Factory** — for creating `Order`s from raw input.
- **Observer** — for notifying on completion.

```java
public final class OrderProcessor {
    private final PricingStrategy pricing;
    private final Consumer<Order> onComplete;

    public OrderProcessor(PricingStrategy pricing, Consumer<Order> onComplete) {
        this.pricing = pricing;
        this.onComplete = onComplete;
    }

    public Order process(long baseCents) {
        Order o = Order.builder().baseCents(baseCents).build();
        o.apply(pricing);
        onComplete.accept(o);
        return o;
    }
}
```

Each pattern does one thing; the *composition* is the real design.

---

## Do the lab

Build a small text-decoration library that uses the Strategy, Decorator,
and Builder patterns. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

Strategy · Decorator · Builder · Factory · Observer · Adapter · Singleton ·
Composite · Visitor · Façade · Dependency Injection · sealed hierarchies
vs. Visitor · `@FunctionalInterface` · `Consumer<T>` listener

**Next →** [Module 15: Capstone — Library Management System](../15-capstone-library/)
