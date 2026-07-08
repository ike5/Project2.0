package com.example.orders;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.OptionalDouble;
import java.util.Random;
import java.util.Set;
import java.util.function.BiConsumer;
import java.util.function.BinaryOperator;
import java.util.function.Function;
import java.util.function.Predicate;
import java.util.function.Supplier;
import java.util.stream.Collector;
import java.util.stream.Collectors;
import java.util.stream.Stream;

public final class Challenge07 {

    private Challenge07() {}

    public static void main(String[] args) {
        // 1. topN
        var words = List.of("the", "cat", "the", "dog", "the", "cat", "bird", "cat");
        System.out.println(topN(words, 2));  // [the=3, cat=3] (or [cat=3, the=3] depending on tiebreak)

        // 2. cleanString
        Function<String, String> clean = cleanString();
        System.out.println(clean.apply("   Hello,   WORLD!!  "));   // "hello, world"

        // 3. median
        System.out.println(Stream.of(1, 2, 3, 4, 5).collect(median()));         // OptionalDouble[3.0]
        System.out.println(Stream.<Integer>of().collect(median()));             // OptionalDouble.empty

        // 4. countryOf
        System.out.println(countryOf(1L).orElse("(none)"));    // "JP"
        System.out.println(countryOf(99L).orElse("(none)"));   // "(none)"

        // 5. takeUntil + randomInts
        var r = new Random(42);
        Supplier<Integer> gen = () -> r.nextInt(100);
        Supplier<Stream<Integer>> stream = () -> Stream.generate(gen).limit(10);
        // Take until we see a value < 50.
        List<Integer> xs = takeUntil(stream.get().toList(), n -> n >= 50);
        System.out.println(xs);
    }

    // 1. topN by frequency (ties broken alphabetically).
    public static List<Map.Entry<String, Long>> topN(List<String> words, int n) {
        Map<String, Long> counts = words.stream().collect(Collectors.groupingBy(w -> w, Collectors.counting()));
        return counts.entrySet().stream()
                .sorted(Comparator.<Map.Entry<String, Long>>comparingLong(Map.Entry::getValue)
                        .reversed()
                        .thenComparing(Map.Entry::getKey))
                .limit(n)
                .toList();
    }

    // 2. cleanString composed from smaller functions.
    public static Function<String, String> cleanString() {
        Function<String, String> trim = String::trim;
        Function<String, String> lower = String::toLowerCase;
        Function<String, String> collapseWs = s -> s.replaceAll("\\s+", " ");
        Function<String, String> stripPunct = s -> s.replaceAll("^[.,!?]+|[.,!?]+$", "");
        return trim.andThen(lower).andThen(collapseWs).andThen(stripPunct);
    }

    // 3. A Collector<Integer, ?, OptionalDouble> for the median.
    public static Collector<Integer, List<Integer>, OptionalDouble> median() {
        Supplier<List<Integer>>        supplier = ArrayList::new;
        BiConsumer<List<Integer>, Integer> accumulator = List::add;
        BinaryOperator<List<Integer>>  combiner = (a, b) -> { a.addAll(b); return a; };
        Function<List<Integer>, OptionalDouble> finisher = xs -> {
            if (xs.isEmpty()) return OptionalDouble.empty();
            Collections.sort(xs);
            int n = xs.size();
            if (n % 2 == 1) return OptionalDouble.of(xs.get(n / 2));
            return OptionalDouble.of((xs.get(n / 2 - 1) + xs.get(n / 2)) / 2.0);
        };
        return Collector.of(supplier, accumulator, combiner, finisher);
    }

    // 4. countryOf chain.
    public record User(long id, Optional<Address> primaryAddress) {}
    public record Address(String countryCode) {}
    public static Optional<User> findUser(long id) {
        if (id == 1) return Optional.of(new User(1, Optional.of(new Address("JP"))));
        return Optional.empty();
    }
    public static Optional<String> countryOf(long userId) {
        return findUser(userId)
                .flatMap(User::primaryAddress)
                .map(Address::countryCode);
    }

    // 5. takeUntil: include elements while the predicate holds, stop at the first false.
    public static <T> List<T> takeUntil(List<T> xs, Predicate<T> p) {
        List<T> out = new ArrayList<>();
        for (T x : xs) {
            if (!p.test(x)) break;
            out.add(x);
        }
        return out;
    }

    // A Supplier-based generator for stream testing.
    public static Supplier<Integer> randomInts(long seed) {
        Random r = new Random(seed);
        return r::nextInt;
    }
}
