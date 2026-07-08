package com.example.registry;

import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

public final class Index<K, V> {
    private final Map<K, List<V>> byKey = new HashMap<>();

    public void add(K key, V value) {
        byKey.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
    }

    public List<V> get(K key) {
        return Collections.unmodifiableList(byKey.getOrDefault(key, List.of()));
    }

    public Set<K> keys() { return Collections.unmodifiableSet(byKey.keySet()); }

    public int size() { return byKey.size(); }
}
