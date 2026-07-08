package com.example.scheduler;

import java.util.ArrayList;
import java.util.concurrent.CompletableFuture;

public class Main {
    public static void main(String[] args) throws Exception {
        var counter = new Counter();
        try (var pool = new WorkerPool(4)) {
            var futures = new ArrayList<CompletableFuture<Void>>();
            for (int t = 0; t < 4; t++) {
                futures.add(pool.submit(() -> {
                    for (int i = 0; i < 1000; i++) counter.increment();
                    return null;
                }));
            }
            CompletableFuture.allOf(futures.toArray(CompletableFuture[]::new)).get();
            System.out.println("counter = " + counter.current() + "  (expected 4000)");

            CompletableFuture<String> result = CompletableFuture
                    .supplyAsync(() -> "user:42", pool.executor())
                    .thenApply(s -> "fetched " + s)
                    .thenApply(String::toUpperCase)
                    .exceptionally(ex -> "fallback: " + ex.getClass().getSimpleName());
            System.out.println("pipeline = " + result.get());

            // Broken counter for contrast.
            var broken = new BrokenCounter();
            var brokenFutures = new ArrayList<CompletableFuture<Void>>();
            for (int t = 0; t < 4; t++) {
                brokenFutures.add(pool.submit(() -> { for (int i = 0; i < 1000; i++) broken.increment(); return null; }));
            }
            CompletableFuture.allOf(brokenFutures.toArray(CompletableFuture[]::new)).get();
            System.out.println("broken = " + broken.current() + "  (expected 4000, will be less)");

            // handle
            CompletableFuture<Integer> f = CompletableFuture
                    .<Integer>supplyAsync(() -> { throw new IllegalStateException("nope"); })
                    .handle((r, ex) -> ex == null ? r : -1);
            System.out.println("recovered: " + f.get());
        }
    }

    public static final class BrokenCounter {
        private long count = 0;
        public void increment() { count++; }
        public long current() { return count; }
    }
}
