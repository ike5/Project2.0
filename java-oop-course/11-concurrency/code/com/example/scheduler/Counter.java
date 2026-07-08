package com.example.scheduler;

import java.util.concurrent.atomic.AtomicLong;

public final class Counter {
    private final AtomicLong count = new AtomicLong();
    public long increment() { return count.incrementAndGet(); }
    public long current()   { return count.get(); }
}
