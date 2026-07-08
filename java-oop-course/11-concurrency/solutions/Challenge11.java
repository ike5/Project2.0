package com.example.scheduler;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;
import java.util.concurrent.atomic.AtomicLong;

public final class Challenge11 {

    private Challenge11() {}

    public static void main(String[] args) throws Exception {
        // 1. AtomicLong counter under contention.
        AtomicLong count = new AtomicLong();
        try (var pool = new WorkerPool(8)) {
            var futures = new ArrayList<CompletableFuture<Void>>();
            for (int t = 0; t < 8; t++) {
                futures.add(pool.submit(() -> { for (int i = 0; i < 10_000; i++) count.incrementAndGet(); return null; }));
            }
            CompletableFuture.allOf(futures.toArray(CompletableFuture[]::new)).get();
            System.out.println("counter = " + count.get() + " (expected 80000)");
        }

        // 2. thenCompose chain.
        var city = fetchUserName(1L)
                .thenCompose(name -> fetchAddress(name))
                .thenApply(Address::city)
                .get();
        System.out.println("user 1 lives in: " + city);

        // 3. thenCombine.
        CompletableFuture<Integer> a = CompletableFuture.supplyAsync(() -> { sleep(100); return 3; });
        CompletableFuture<Integer> b = CompletableFuture.supplyAsync(() -> { sleep(100); return 4; });
        long t0 = System.currentTimeMillis();
        int sum = a.thenCombine(b, Integer::sum).get();
        long elapsed = System.currentTimeMillis() - t0;
        System.out.println("sum = " + sum + " in " + elapsed + " ms (parallel, ~100ms)");

        // 4. Producer / consumer.
        var pc = new ProducerConsumer();
        pc.start();
        pc.stop();

        // 5. ConcurrentHashMap computeIfAbsent.
        ConcurrentMap<String, List<String>> byTag = new ConcurrentHashMap<>();
        try (var pool = new WorkerPool(4)) {
            var futures2 = new ArrayList<CompletableFuture<Void>>();
            for (int i = 0; i < 4; i++) {
                int t = i;
                futures2.add(pool.submit(() -> {
                    add(byTag, "java", "thread-" + t);
                    add(byTag, "java", "task-"   + t);
                    return null;
                }));
            }
            CompletableFuture.allOf(futures2.toArray(CompletableFuture[]::new)).get();
            System.out.println("byTag keys: " + byTag.keySet());
            System.out.println("java bucket: " + byTag.get("java"));
        }
    }

    // 2. fetchUserName + fetchAddress (synthetic).
    public static CompletableFuture<String> fetchUserName(long id) {
        return CompletableFuture.completedFuture(id == 1 ? "Ada Lovelace" : "Grace Hopper");
    }
    public record Address(String city) {}
    public static CompletableFuture<Address> fetchAddress(String name) {
        return CompletableFuture.completedFuture(new Address(name.startsWith("Ada") ? "London" : "New York"));
    }

    // 4. Producer / consumer.
    public static final class ProducerConsumer {
        private final BlockingQueue<Integer> queue = new ArrayBlockingQueue<>(16);
        private Thread producer, consumer;
        public void start() {
            producer = new Thread(() -> {
                try {
                    for (int i = 0; i < 100; i++) { queue.put(i); Thread.sleep(2); }
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }, "producer");
            consumer = new Thread(() -> {
                try {
                    for (int i = 0; i < 100; i++) System.out.println("  consumed " + queue.take());
                } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
            }, "consumer");
            producer.start();
            consumer.start();
        }
        public void stop() throws InterruptedException {
            producer.join();
            consumer.join();
        }
    }

    // 5. computeIfAbsent add.
    public static void add(ConcurrentMap<String, List<String>> map, String tag, String value) {
        map.computeIfAbsent(tag, t -> new ArrayList<>()).add(value);
    }

    private static void sleep(long ms) {
        try { Thread.sleep(ms); } catch (InterruptedException e) { Thread.currentThread().interrupt(); }
    }
}
