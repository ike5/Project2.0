package com.example.registry;

import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.PriorityQueue;
import java.util.Set;
import java.util.TreeSet;

public final class Challenge06 {

    private Challenge06() {}

    public static void main(String[] args) {
        // 1. wordCount
        String text = "The quick brown fox jumps over the lazy dog. The dog barks.";
        System.out.println(wordCount(text).get("the"));   // 3
        System.out.println(wordCount(text).get("dog"));   // 2

        // 2. LRU
        LruCache<Integer, String> cache = new LruCache<>(3);
        cache.put(1, "a"); cache.put(2, "b"); cache.put(3, "c");
        cache.get(1);
        cache.put(4, "d");   // evicts 2 (the LRU not recently accessed)
        System.out.println(cache.keySet());  // [1, 3, 4] in some order

        // 3. MultiMap
        MultiMap<String, Integer> mm = new MultiMap<>();
        mm.add("a", 1); mm.add("a", 2); mm.add("b", 3);
        System.out.println(mm.get("a"));   // [1, 2]
        try { mm.get("a").add(99); }
        catch (UnsupportedOperationException e) { System.out.println("rejected: mutation"); }
        mm.remove("a", 1);
        System.out.println(mm.get("a"));   // [2]

        // 4. PriorityQueue
        List<Task> tasks = List.of(
                new Task("compile", 5),
                new Task("test",    3),
                new Task("deploy",  9),
                new Task("lint",    1)
        );
        System.out.println(schedule(tasks));
    }

    // 1. Word count.
    public static Map<String, Long> wordCount(String text) {
        Map<String, Long> counts = new HashMap<>();
        for (String w : text.toLowerCase().split("[^a-z0-9]+")) {
            if (w.isEmpty()) continue;
            counts.merge(w, 1L, Long::sum);
        }
        return counts;
    }

    // 2. LRU cache: removeEldestEntry returns true when size > capacity.
    public static final class LruCache<K, V> extends LinkedHashMap<K, V> {
        private final int capacity;
        public LruCache(int capacity) {
            super(16, 0.75f, /* accessOrder = */ true);
            this.capacity = capacity;
        }
        @Override protected boolean removeEldestEntry(Map.Entry<K, V> eldest) {
            return size() > capacity;
        }
    }

    // 3. MultiMap.
    public static final class MultiMap<K, V> {
        private final Map<K, List<V>> byKey = new HashMap<>();
        public void add(K key, V value) {
            byKey.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
        }
        public List<V> get(K key) {
            return Collections.unmodifiableList(byKey.getOrDefault(key, List.of()));
        }
        public Set<K> keys() { return Collections.unmodifiableSet(byKey.keySet()); }
        public boolean remove(K key, V value) {
            List<V> bucket = byKey.get(key);
            if (bucket == null) return false;
            boolean removed = bucket.remove(value);
            if (bucket.isEmpty()) byKey.remove(key);
            return removed;
        }
    }

    // 4. PriorityQueue scheduling.
    public record Task(String name, int deadline) {}
    public static List<Task> schedule(List<Task> tasks) {
        PriorityQueue<Task> pq = new PriorityQueue<>(Comparator.comparingInt(Task::deadline));
        pq.addAll(tasks);
        List<Task> ordered = new ArrayList<>(tasks.size());
        while (!pq.isEmpty()) ordered.add(pq.poll());
        return ordered;
    }
}
