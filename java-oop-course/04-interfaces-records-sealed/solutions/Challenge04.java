package com.example.payments;

import java.util.Currency;
import java.util.List;
import java.util.Objects;

public final class Challenge04 {

    private Challenge04() {}

    public static void main(String[] args) {
        // 1. Result<T>.
        Result<String> ok  = Result.ok("hi");
        Result<String> err = Result.error("not found", new IllegalStateException("missing"));
        System.out.println(render(ok));
        System.out.println(render(err));

        // 2. Money.
        Money a = new Money(12_34, Currency.getInstance("USD"));
        Money b = new Money(5_00,  Currency.getInstance("USD"));
        System.out.println(a.add(b));
        try { a.add(new Money(1, Currency.getInstance("EUR"))); }
        catch (IllegalArgumentException e) { System.out.println("rejected: " + e.getMessage()); }

        // 3. Sealed shape.
        List<Shape> shapes = List.of(
                new Circle(2.0),
                new Rectangle(3.0, 4.0),
                new Triangle(3.0, 4.0, 5.0)
        );
        shapes.forEach(s -> System.out.println(s.describe()));

        // 4. describeShape on Object.
        Object o = shapes.get(0);
        System.out.println(describeShape(o));
        System.out.println(describeShape("hello"));
    }

    // 1. Result<T> sum type.
    public sealed interface Result<T> permits Result.Success, Result.Failure {
        static <T> Result<T> ok(T value) { return new Success<>(value); }
        static <T> Result<T> error(String message, Throwable cause) { return new Failure<>(message, cause); }

        record Success<T>(T value) implements Result<T> { }
        record Failure<T>(String message, Throwable cause) implements Result<T> {
            public Failure { Objects.requireNonNull(cause, "cause"); }
        }
    }

    public static String render(Result<String> r) {
        return switch (r) {
            case Result.Success<String> s -> "OK: " + s.value();
            case Result.Failure<String> f -> "ERR: " + f.message();
        };
    }

    // 2. Money.
    public record Money(long cents, Currency currency) {
        public Money {
            Objects.requireNonNull(currency, "currency");
            if (cents < 0) throw new IllegalArgumentException("cents must be >= 0");
        }
        public Money add(Money other) {
            if (!currency.equals(other.currency)) {
                throw new IllegalArgumentException("currency mismatch: " + currency + " vs " + other.currency);
            }
            return new Money(cents + other.cents, currency);
        }
        @Override public String toString() {
            return "$%d.%02d %s".formatted(cents / 100, Math.abs(cents % 100), currency.getCurrencyCode());
        }
    }

    // 3. Sealed Shape.
    public sealed interface Shape permits Circle, Rectangle, Triangle {
        String kind();
        default String describe() { return "A %s".formatted(kind()); }
    }
    public record Circle(double radius) implements Shape {
        public Circle { if (radius <= 0) throw new IllegalArgumentException("radius > 0"); }
        @Override public String kind() { return "circle with r=" + radius; }
    }
    public record Rectangle(double width, double height) implements Shape {
        public Rectangle { if (width <= 0 || height <= 0) throw new IllegalArgumentException("sides > 0"); }
        @Override public String kind() { return "rectangle " + width + "x" + height; }
    }
    public record Triangle(double a, double b, double c) implements Shape {
        public Triangle {
            if (a <= 0 || b <= 0 || c <= 0 || a + b <= c || a + c <= b || b + c <= a) {
                throw new IllegalArgumentException("invalid triangle");
            }
        }
        @Override public String kind() { return "triangle " + a + "," + b + "," + c; }
    }

    // 4. describeShape on Object.
    public static String describeShape(Object o) {
        if (o instanceof Circle c)    return "circle r=" + c.radius();
        if (o instanceof Rectangle r) return "rectangle " + r.width() + "x" + r.height();
        if (o instanceof Triangle t)  return "triangle " + t.a() + "," + t.b() + "," + t.c();
        return "not a shape";
    }
}
