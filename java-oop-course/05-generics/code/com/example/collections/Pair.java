package com.example.collections;

import java.util.Map;

public record Pair<K, V>(K key, V value) {
    public Pair {
        if (key == null) throw new IllegalArgumentException("key required");
    }

    public static <K, V> Pair<K, V> of(K key, V value) { return new Pair<>(key, value); }

    public static <K, V> void putIfAbsent(
            Map<K, V> map, Pair<? extends K, ? extends V> entry) {
        map.putIfAbsent(entry.key(), entry.value());
    }
}
