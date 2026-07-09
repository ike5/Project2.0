package com.example.patterns;

import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Consumer;

public final class EventBus<T> {
    private final List<Consumer<T>> listeners = new CopyOnWriteArrayList<>();

    public Runnable subscribe(Consumer<T> listener) {
        listeners.add(listener);
        return () -> listeners.remove(listener);
    }

    public void publish(T event) {
        for (var l : listeners) l.accept(event);
    }
}
