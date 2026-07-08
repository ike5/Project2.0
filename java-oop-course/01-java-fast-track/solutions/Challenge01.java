package com.example.ft01;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Objects;

public final class Challenge01 {

    private Challenge01() {}

    public static void main(String[] args) {
        // 1. BUG: mutates the caller's list.
        List<Integer> input = new ArrayList<>(List.of(1, 2, 3));
        addOneBuggy(input);
        System.out.println("after buggy: " + input);   // [2, 3, 4]   (oops)

        // FIX: return a new list.
        List<Integer> safe = new ArrayList<>(List.of(1, 2, 3));
        List<Integer> out  = addOne(safe);
        System.out.println("input untouched: " + safe + " | result: " + out);

        // 2. Null-safe lookup.
        Map<String, String> cfg = Map.of("env", "dev");
        System.out.println(getOrDefault(cfg, "missing", "n/a"));  // n/a

        // 3. Classify.
        System.out.println(grade(95));    // A
        System.out.println(grade(150));   // invalid
        System.out.println(grade(-1));    // invalid

        // 4. Describe.
        System.out.println(describe(42));                       // int: 42
        System.out.println(describe("hi"));                     // string: hi
        System.out.println(describe(List.of(1, 2, 3)));         // list: 3
        System.out.println(describe(null));                     // null
        System.out.println(describe(3.14));                     // unknown: Double
    }

    // 1. BUG: mutates the caller's list.
    public static void addOneBuggy(List<Integer> xs) {
        for (int i = 0; i < xs.size(); i++) {
            xs.set(i, xs.get(i) + 1);
        }
    }

    // FIX: stream pipeline returns a new list.
    public static List<Integer> addOne(List<Integer> xs) {
        return xs.stream().map(n -> n + 1).toList();
    }

    // 2. Null-safe lookup using Map.getOrDefault.
    public static String getOrDefault(Map<String, String> config,
                                      String key, String fallback) {
        Objects.requireNonNull(config, "config");
        Objects.requireNonNull(key, "key");
        Objects.requireNonNull(fallback, "fallback");
        return config.getOrDefault(key, fallback);
    }

    // 3. Switch expression over an int. The `case` form takes a constant expression;
    //    for guard logic, switch on Integer (autoboxed) and use `when`.
    public static String grade(int score) {
        return switch (Integer.valueOf(score)) {
            case Integer s when s < 0 || s > 100 -> "invalid";
            case Integer s when s >= 90          -> "A";
            case Integer s when s >= 80          -> "B";
            case Integer s when s >= 70          -> "C";
            default                               -> "F";
        };
    }

    // 4. Pattern matching.
    public static String describe(Object o) {
        if (o == null) return "null";
        if (o instanceof Integer i) return "int: " + i;
        if (o instanceof String s)  return "string: " + s;
        if (o instanceof List<?> l) return "list: " + l.size();
        return "unknown: " + o.getClass().getSimpleName();
    }
}
