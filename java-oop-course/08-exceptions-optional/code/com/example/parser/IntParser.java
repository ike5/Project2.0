package com.example.parser;

import java.util.OptionalInt;

public final class IntParser {
    private IntParser() {}

    public static OptionalInt tryParse(String s) {
        if (s == null) return OptionalInt.empty();
        try {
            return OptionalInt.of(Integer.parseInt(s.trim()));
        } catch (NumberFormatException e) {
            return OptionalInt.empty();
        }
    }

    public static int parseOrThrow(String s) {
        return tryParse(s).orElseThrow(() ->
                new IllegalArgumentException("not an int: " + s));
    }
}
