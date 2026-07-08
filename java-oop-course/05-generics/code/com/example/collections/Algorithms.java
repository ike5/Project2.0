package com.example.collections;

import java.util.Collection;
import java.util.Comparator;

public final class Algorithms {
    private Algorithms() {}

    public static <T extends Comparable<T>> T max(Collection<T> xs) {
        if (xs.isEmpty()) throw new IllegalArgumentException("empty");
        T best = xs.iterator().next();
        for (T x : xs) if (x.compareTo(best) > 0) best = x;
        return best;
    }

    public static <T> T max(Collection<T> xs, Comparator<T> cmp) {
        if (xs.isEmpty()) throw new IllegalArgumentException("empty");
        T best = xs.iterator().next();
        for (T x : xs) if (cmp.compare(x, best) > 0) best = x;
        return best;
    }
}
