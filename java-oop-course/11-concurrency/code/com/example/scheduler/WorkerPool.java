package com.example.scheduler;

import java.util.concurrent.Callable;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class WorkerPool implements AutoCloseable {
    private final ExecutorService pool;

    public WorkerPool(int n) { this.pool = Executors.newFixedThreadPool(n); }

    public <T> CompletableFuture<T> submit(Callable<T> task) {
        return CompletableFuture.supplyAsync(() -> {
            try { return task.call(); }
            catch (Exception e) { throw new RuntimeException(e); }
        }, pool);
    }

    public ExecutorService executor() { return pool; }

    public void shutdown() throws InterruptedException {
        pool.shutdown();
        if (!pool.awaitTermination(5, TimeUnit.SECONDS)) pool.shutdownNow();
    }

    @Override public void close() throws Exception { shutdown(); }
}
