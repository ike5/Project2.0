package com.example.collections;

import java.util.Collection;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.Optional;

public final class Challenge05 {

    private Challenge05() {}

    public static void main(String[] args) {
        // 1. getOr with Result.
        var m = new java.util.HashMap<String, Integer>();
        m.put("a", 1);
        System.out.println(getOr(m, "a", 99));   // Success(1)
        System.out.println(getOr(m, "z", 99));   // Failure

        // 2. min/max.
        System.out.println(min(List.of(3, 1, 4), Integer::compare).orElseThrow());   // 1
        System.out.println(max(List.of(3, 1, 4), Integer::compare).orElseThrow());   // 4
        System.out.println(min(List.<Integer>of(), Integer::compare));               // Optional.empty

        // 3. mergeMaps.
        Map<Object, Object> target = new java.util.HashMap<>();
        Map<String, Integer> source = Map.of("a", 1, "b", 2);
        mergeMaps(target, source);
        System.out.println(target);

        // 4. Either.
        Either<String, Integer> ok  = new Right<String, Integer>(42);
        Either<String, Integer> bad = new Left<String, Integer>("missing");
        System.out.println(orElse(ok,  -1));   // 42
        System.out.println(orElse(bad, -1));   // -1

        // 5. Uncommenting the line below will not compile:
        // addWildcard(List.of(1, 2, 3), 4);
    }

    // 1. getOr with Result.
    public static <K, V> Result<V> getOr(Map<K, V> map, K key, V fallback) {
        V value = map.get(key);
        return value != null ? Result.ok(value) : Result.error("key not found: " + key, new IllegalStateException("absent"));
    }

    public sealed interface Result<T> permits ResultOk, ResultErr {
        static <T> Result<T> ok(T value)        { return new ResultOk<>(value); }
        static <T> Result<T> error(String m, Throwable c) { return new ResultErr<>(m, c); }
    }
    public record ResultOk<T>(T value)         implements Result<T> {}
    public record ResultErr<T>(String message, Throwable cause) implements Result<T> {
        public ResultErr { Objects.requireNonNull(cause, "cause"); }
    }

    // 2. min/max returning Optional.
    public static <T> Optional<T> min(Collection<T> xs, Comparator<T> cmp) {
        return xs.stream().min(cmp);
    }
    public static <T> Optional<T> max(Collection<T> xs, Comparator<T> cmp) {
        return xs.stream().max(cmp);
    }

    // 3. mergeMaps with PECS.
    public static <K, V> void mergeMaps(Map<K, V> target, Map<? extends K, ? extends V> source) {
        source.forEach(target::putIfAbsent);
    }

    // 4. Either sum type. Each variant carries exactly one payload, so each
    //    is parameterised on just the type of that payload; the parent
    //    interface carries the full L,R pair.
    public sealed interface Either<L, R> permits Left, Right { }
    public record Left<L, R>(L value)  implements Either<L, R> {}
    public record Right<L, R>(R value) implements Either<L, R> {}
    public static <L, R> R orElse(Either<L, R> e, R fallback) {
        return switch (e) {
            case Right<L, R> r -> r.value();
            case Left<L, R> ignored -> fallback;
        };
    }

    // 5. The wildcard can't be added to. Reference: List<Integer> is not
    //    a List<Number>, so the runtime type of 'xs' could be List<Integer>,
    //    List<Double>, etc. The compiler can't prove that adding an Integer
    //    is safe.
    public static void addWildcard(java.util.List<? extends Number> xs, Integer i) {
        // xs.add(i);  // compile error: incompatible types
    }
}
