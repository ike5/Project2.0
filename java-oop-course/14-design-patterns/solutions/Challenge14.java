package com.example.patterns;

import java.math.BigDecimal;
import java.util.List;
import java.util.Optional;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.function.Consumer;

public final class Challenge14 {

    private Challenge14() {}

    public static void main(String[] args) throws Exception {
        // 1. Discount + Cart.
        var cart = new Cart(new BigDecimal("100.00"), Discount.percentage(new BigDecimal("0.10")));
        System.out.println("cart total: " + cart.total());

        // 2. LoggingRepository.
        var inMemory = new InMemoryRepository<String, Long>(List.of("a", "b", "c"));
        var logged   = new LoggingRepository<>(inMemory);
        logged.findById(1L);
        logged.findAll();

        // 3. MoneyBuilder.
        Money m = MoneyBuilder.usd(10_00).plus(MoneyBuilder.usd(5_00).build()).minus(MoneyBuilder.usd(2_00).build()).build();
        System.out.println("money: " + m);

        // 4. Shape factory.
        System.out.println(Shape.of("circle", 2.0).render());
        System.out.println(Shape.of("rect", 3.0, 4.0).render());

        // 5. Ticker.
        Ticker t = new Ticker();
        Runnable stop = t.subscribe(System.out::println);
        t.start(50);
        Thread.sleep(180);
        stop.run();
        t.stop();

        // 6. Singleton.
        System.out.println(AppConfig.get() == AppConfig.get());   // true
    }

    // 1. Discount.
    public interface Discount { BigDecimal apply(BigDecimal price);
        static Discount none() { return p -> p; }
        static Discount percentage(BigDecimal rate) { return p -> p.multiply(BigDecimal.ONE.subtract(rate)); }
        static Discount bulk(BigDecimal threshold, BigDecimal percent) {
            return p -> p.compareTo(threshold) >= 0
                    ? p.multiply(BigDecimal.ONE.subtract(percent))
                    : p;
        }
    }
    public record Cart(BigDecimal total, Discount discount) {
        public BigDecimal total() { return discount.apply(total); }
    }

    // 2. Repository + LoggingRepository.
    public interface Repository<T, ID> { Optional<T> findById(ID id); List<T> findAll(); }
    public static final class InMemoryRepository<T, ID> implements Repository<T, ID> {
        private final List<T> items;
        public InMemoryRepository(List<T> items) { this.items = List.copyOf(items); }
        @Override public Optional<T> findById(ID id) { return items.stream().findFirst(); }
        @Override public List<T> findAll() { return items; }
    }
    public static final class LoggingRepository<T, ID> implements Repository<T, ID> {
        private final Repository<T, ID> delegate;
        public LoggingRepository(Repository<T, ID> delegate) { this.delegate = delegate; }
        @Override public Optional<T> findById(ID id) {
            System.out.println("[repo] findById(" + id + ")");
            return delegate.findById(id);
        }
        @Override public List<T> findAll() {
            System.out.println("[repo] findAll()");
            return delegate.findAll();
        }
    }

    // 3. MoneyBuilder.
    public record Money(long cents, String currency) {
        public Money plus(Money o)   { if (!currency.equals(o.currency)) throw new IllegalArgumentException("currency mismatch"); return new Money(cents + o.cents, currency); }
        public Money minus(Money o)  { if (!currency.equals(o.currency)) throw new IllegalArgumentException("currency mismatch"); return new Money(cents - o.cents, currency); }
        public static MoneyBuilder usd(long cents) { return new MoneyBuilder(cents, "USD"); }
        @Override public String toString() { return "$" + (cents / 100.0) + " " + currency; }
    }
    public static final class MoneyBuilder {
        private long cents;
        private final String currency;
        public MoneyBuilder(long cents, String currency) { this.cents = cents; this.currency = currency; }
        public MoneyBuilder plus(Money other)  { this.cents += other.cents(); return this; }
        public MoneyBuilder minus(Money other) { this.cents -= other.cents(); return this; }
        public Money build() { return new Money(cents, currency); }
        public static MoneyBuilder usd(long cents) { return Money.usd(cents); }
    }

    // 4. Shape factory.
    public sealed interface Shape permits Shape.Circle, Shape.Rect, Shape.Tri {
        String render();
        record Circle(double r) implements Shape { public String render() { return "circle r=" + r; } }
        record Rect(double w, double h) implements Shape { public String render() { return "rect " + w + "x" + h; } }
        record Tri(double a, double b, double c) implements Shape { public String render() { return "triangle"; } }

        static Shape of(String kind, double... dims) {
            return switch (kind) {
                case "circle" -> new Circle(dims[0]);
                case "rect"   -> new Rect(dims[0], dims[1]);
                case "tri"    -> new Tri(dims[0], dims[1], dims[2]);
                default -> throw new IllegalArgumentException("unknown: " + kind);
            };
        }
    }

    // 5. Ticker.
    public static final class Ticker {
        private final List<Consumer<Long>> listeners = new CopyOnWriteArrayList<>();
        private ScheduledExecutorService scheduler;
        private long tick = 0;
        public Runnable subscribe(Consumer<Long> listener) {
            listeners.add(listener);
            return () -> listeners.remove(listener);
        }
        public void start(long periodMs) {
            scheduler = Executors.newSingleThreadScheduledExecutor();
            scheduler.scheduleAtFixedRate(() -> {
                tick++;
                for (var l : listeners) l.accept(tick);
            }, 0, periodMs, TimeUnit.MILLISECONDS);
        }
        public void stop() { if (scheduler != null) scheduler.shutdownNow(); }
    }

    // 6. Singleton.
    public static final class AppConfig {
        private static final AppConfig INSTANCE = new AppConfig("production", 8080);
        private final String env;
        private final int port;
        private AppConfig(String env, int port) { this.env = env; this.port = port; }
        public static AppConfig get() { return INSTANCE; }
        public String env() { return env; }
        public int port() { return port; }
    }
}
